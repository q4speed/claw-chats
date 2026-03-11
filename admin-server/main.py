"""
ClawChats Admin Server - Phase 3
管理员用户创建系统 - 关闭普通注册，仅管理员可创建用户
"""

import os
import re
import uuid
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator
import asyncpg
from jose import JWTError, jwt

# Configuration
PORT = int(os.getenv("PORT", "8766"))
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/clawchats"
)
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# FastAPI app
app = FastAPI(title="ClawChats Admin Server", version="0.3.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Database pool
db_pool: Optional[asyncpg.Pool] = None


# ============== Pydantic Models ==============

class AdminLogin(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    
    @validator('username')
    def validate_username(cls, v):
        # 用户名：6-20 位，字母数字下划线，不能以数字开头
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]{5,19}$', v):
            raise ValueError('用户名长度 6-20 位，仅支持字母、数字、下划线，不能以数字开头')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        # 密码：8-16 位，包含大写 + 小写 + 数字 + 特殊符号
        if len(v) < 8 or len(v) > 16:
            raise ValueError('密码长度必须为 8-16 位')
        if not re.search(r'[A-Z]', v):
            raise ValueError('密码必须包含大写字母')
        if not re.search(r'[a-z]', v):
            raise ValueError('密码必须包含小写字母')
        if not re.search(r'[0-9]', v):
            raise ValueError('密码必须包含数字')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('密码必须包含特殊符号（!@#$%^&* 等）')
        return v


class Token(BaseModel):
    access_token: str
    token_type: str
    admin_id: str
    username: str
    role: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str]
    status: str
    created_at: datetime
    created_by: Optional[str]


class AdminCreateUserResult(BaseModel):
    message: str
    user_id: str
    username: str
    temporary_password: str  # 初始密码（用于交付）


# ============== Database Functions ==============

async def get_db():
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(DATABASE_URL)
    return db_pool


async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL)
    print("[DB] Connection pool created")


# ============== Authentication ==============

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证管理员身份"""
    db = await get_db()
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        admin_id = payload.get("sub")
        if admin_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    admin = await db.fetchrow(
        "SELECT id, username, role FROM admins WHERE id = $1 AND status = 'active'",
        admin_id
    )
    
    if not admin:
        raise HTTPException(status_code=401, detail="管理员不存在或已禁用")
    
    return admin


# ============== API Routes ==============

@app.on_event("startup")
async def startup_event():
    await init_db()
    print(f"🚀 Admin Server starting on port {PORT}...")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# ============== Admin Authentication ==============

@app.post("/api/v1/admin/login")
async def admin_login(credentials: AdminLogin):
    """管理员登录"""
    db = await get_db()
    
    admin = await db.fetchrow(
        "SELECT id, username, password_hash, role FROM admins WHERE username = $1 AND status = 'active'",
        credentials.username
    )
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if not verify_password(credentials.password, admin["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    access_token = create_access_token(
        data={"sub": admin["id"], "username": admin["username"], "role": admin["role"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "admin_id": admin["id"],
        "username": admin["username"],
        "role": admin["role"]
    }


# ============== User Management (Admin Only) ==============

@app.post("/api/v1/admin/users", status_code=status.HTTP_201_CREATED)
async def admin_create_user(
    user_data: UserCreate,
    current_admin: dict = Depends(get_current_admin)
):
    """
    管理员创建用户
    - 关闭普通用户注册
    - 仅管理员可创建
    - 用户名/密码规范校验
    - 用户名唯一性校验
    """
    db = await get_db()
    
    # 用户名唯一性校验（检查普通用户表和管理员表）
    existing_user = await db.fetchrow(
        "SELECT id FROM users WHERE username = $1",
        user_data.username
    )
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该用户名已存在，请更换其他用户名"
        )
    
    # 检查管理员表
    existing_admin = await db.fetchrow(
        "SELECT id FROM admins WHERE username = $1",
        user_data.username
    )
    
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该用户名已存在，请更换其他用户名"
        )
    
    # 创建用户
    user_id = f"user-{uuid.uuid4().hex[:12]}"
    password_hash = get_password_hash(user_data.password)
    
    try:
        await db.execute(
            """
            INSERT INTO users (id, username, password_hash, email, created_by, status, created_at)
            VALUES ($1, $2, $3, $4, $5, 'active', NOW())
            """,
            user_id, user_data.username, password_hash, user_data.email, current_admin["id"]
        )
        
        return {
            "message": "用户创建成功",
            "user_id": user_id,
            "username": user_data.username,
            "temporary_password": user_data.password,  # 初始密码（管理员需线下交付）
            "created_by": current_admin["username"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建失败：{str(e)}"
        )


@app.get("/api/v1/admin/users")
async def list_users(
    current_admin: dict = Depends(get_current_admin),
    status_filter: Optional[str] = None
):
    """获取用户列表（管理员专用）"""
    db = await get_db()
    
    if status_filter:
        users = await db.fetch(
            """
            SELECT u.id, u.username, u.email, u.status, u.created_at, u.created_by, a.username as creator_name
            FROM users u
            LEFT JOIN admins a ON u.created_by = a.id
            WHERE u.status = $1
            ORDER BY u.created_at DESC
            """,
            status_filter
        )
    else:
        users = await db.fetch(
            """
            SELECT u.id, u.username, u.email, u.status, u.created_at, u.created_by, a.username as creator_name
            FROM users u
            LEFT JOIN admins a ON u.created_by = a.id
            ORDER BY u.created_at DESC
            """
        )
    
    return [dict(user) for user in users]


@app.get("/api/v1/admin/users/{user_id}")
async def get_user(
    user_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """获取用户详情（管理员专用）"""
    db = await get_db()
    
    user = await db.fetchrow(
        """
        SELECT u.id, u.username, u.email, u.status, u.created_at, u.created_by, a.username as creator_name
        FROM users u
        LEFT JOIN admins a ON u.created_by = a.id
        WHERE u.id = $1
        """,
        user_id
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return dict(user)


@app.delete("/api/v1/admin/users/{user_id}")
async def delete_user(
    user_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """删除用户（管理员专用）"""
    db = await get_db()
    
    await db.execute("DELETE FROM users WHERE id = $1", user_id)
    
    return {"message": "用户已删除"}


@app.post("/api/v1/admin/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """切换用户状态（激活/禁用）"""
    db = await get_db()
    
    user = await db.fetchrow("SELECT status FROM users WHERE id = $1", user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    new_status = 'disabled' if user['status'] == 'active' else 'active'
    
    await db.execute(
        "UPDATE users SET status = $1, updated_at = NOW() WHERE id = $2",
        new_status, user_id
    )
    
    return {"message": f"用户已{new_status}", "new_status": new_status}


# ============== Username Validation API ==============

@app.get("/api/v1/admin/users/check-username/{username}")
async def check_username_availability(
    username: str,
    current_admin: dict = Depends(get_current_admin)
):
    """
    实时校验用户名唯一性
    返回：available=true(可用) | available=false(已存在)
    """
    db = await get_db()
    
    # 检查普通用户表
    existing_user = await db.fetchrow(
        "SELECT id FROM users WHERE username = $1",
        username
    )
    
    if existing_user:
        return {"available": False, "message": "该用户名已存在，请更换其他用户名"}
    
    # 检查管理员表
    existing_admin = await db.fetchrow(
        "SELECT id FROM admins WHERE username = $1",
        username
    )
    
    if existing_admin:
        return {"available": False, "message": "该用户名已存在，请更换其他用户名"}
    
    return {"available": True, "message": "用户名可用"}


# ============== Deprecated: Public Registration (Removed) ==============
# 普通用户注册已关闭，仅管理员可创建用户
# POST /api/v1/auth/register - REMOVED


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
