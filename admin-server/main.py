"""
ClawChats Admin Server - Phase 2
REST API for user registration, authentication, and group management
"""

import os
import uuid
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
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
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# FastAPI app
app = FastAPI(title="ClawChats Admin Server", version="0.2.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database pool
db_pool: Optional[asyncpg.Pool] = None


# ============== Pydantic Models ==============

class UserRegister(BaseModel):
    username: str
    password: str
    email: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    username: str


class UserSearch(BaseModel):
    username: str


class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None


class GroupMemberAdd(BaseModel):
    username: str


class GroupMemberRemove(BaseModel):
    user_id: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str]
    created_at: datetime


class GroupResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    owner_id: str
    created_at: datetime
    member_count: int


class GroupMemberResponse(BaseModel):
    user_id: str
    username: str
    role: str
    joined_at: datetime


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
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(lambda: None)) -> Optional[dict]:
    # Simplified for now - will implement proper token validation
    return None


# ============== API Routes ==============

@app.on_event("startup")
async def startup_event():
    await init_db()
    print(f"🚀 Admin Server starting on port {PORT}...")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/api/v1/auth/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """用户注册"""
    db = await get_db()
    
    # Validate username length
    if len(user_data.username) < 3 or len(user_data.username) > 64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名长度必须在 3-64 个字符之间"
        )
    
    # Validate password complexity
    if len(user_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码长度至少为 6 个字符"
        )
    
    # Check username uniqueness
    existing = await db.fetchrow(
        "SELECT id FROM users WHERE username = $1",
        user_data.username
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该用户名已存在，请更换其他用户名"
        )
    
    # Create user
    user_id = f"user-{uuid.uuid4().hex[:12]}"
    password_hash = get_password_hash(user_data.password)
    
    try:
        await db.execute(
            """
            INSERT INTO users (id, username, password_hash, email, created_at)
            VALUES ($1, $2, $3, $4, NOW())
            """,
            user_id, user_data.username, password_hash, user_data.email
        )
        
        return {
            "message": "注册成功",
            "user_id": user_id,
            "username": user_data.username
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败：{str(e)}"
        )


@app.post("/api/v1/auth/login")
async def login(credentials: UserLogin):
    """用户登录"""
    db = await get_db()
    
    # Find user by username
    user = await db.fetchrow(
        "SELECT id, username, password_hash, email FROM users WHERE username = $1 AND status = 'active'",
        credentials.username
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # Verify password
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # Generate token
    access_token = create_access_token(
        data={"sub": user["id"], "username": user["username"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user["id"],
        "username": user["username"]
    }


@app.get("/api/v1/users/search")
async def search_users(q: str):
    """搜索用户"""
    db = await get_db()
    
    users = await db.fetch(
        """
        SELECT id, username, email, created_at
        FROM users
        WHERE username ILIKE $1 AND status = 'active'
        LIMIT 20
        """,
        f"%{q}%"
    )
    
    return [dict(user) for user in users]


@app.get("/api/v1/users/{user_id}")
async def get_user(user_id: str):
    """获取用户信息"""
    db = await get_db()
    
    user = await db.fetchrow(
        "SELECT id, username, email, created_at FROM users WHERE id = $1",
        user_id
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return dict(user)


# ============== Group Management ==============

@app.post("/api/v1/groups", status_code=status.HTTP_201_CREATED)
async def create_group(group_data: GroupCreate, owner_id: str = "user-1"):
    """创建群组"""
    db = await get_db()
    
    group_id = f"group-{uuid.uuid4().hex[:12]}"
    
    try:
        async with db.transaction():
            # Create group
            await db.execute(
                """
                INSERT INTO groups (id, name, description, owner_id, created_at)
                VALUES ($1, $2, $3, $4, NOW())
                """,
                group_id, group_data.name, group_data.description, owner_id
            )
            
            # Add owner as admin
            await db.execute(
                """
                INSERT INTO group_members (group_id, user_id, role, joined_at)
                VALUES ($1, $2, 'admin', NOW())
                """,
                group_id, owner_id
            )
        
        return {
            "message": "群组创建成功",
            "group_id": group_id,
            "name": group_data.name
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建失败：{str(e)}"
        )


@app.get("/api/v1/groups/{group_id}")
async def get_group(group_id: str):
    """获取群组信息"""
    db = await get_db()
    
    group = await db.fetchrow(
        """
        SELECT g.id, g.name, g.description, g.owner_id, g.created_at,
               COUNT(m.user_id) as member_count
        FROM groups g
        LEFT JOIN group_members m ON g.id = m.group_id
        WHERE g.id = $1
        GROUP BY g.id
        """,
        group_id
    )
    
    if not group:
        raise HTTPException(status_code=404, detail="群组不存在")
    
    return dict(group)


@app.get("/api/v1/groups/{group_id}/members")
async def get_group_members(group_id: str):
    """获取群成员列表"""
    db = await get_db()
    
    members = await db.fetch(
        """
        SELECT m.user_id, u.username, m.role, m.joined_at
        FROM group_members m
        JOIN users u ON m.user_id = u.id
        WHERE m.group_id = $1
        ORDER BY m.joined_at
        """,
        group_id
    )
    
    return [dict(member) for member in members]


@app.post("/api/v1/groups/{group_id}/members/add")
async def add_group_member(group_id: str, member_data: GroupMemberAdd):
    """添加群成员"""
    db = await get_db()
    
    # Find user by username
    user = await db.fetchrow(
        "SELECT id FROM users WHERE username = $1 AND status = 'active'",
        member_data.username
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    try:
        await db.execute(
            """
            INSERT INTO group_members (group_id, user_id, role, joined_at)
            VALUES ($1, $2, 'member', NOW())
            ON CONFLICT (group_id, user_id) DO NOTHING
            """,
            group_id, user["id"]
        )
        
        return {"message": "添加成功", "user_id": user["id"]}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加失败：{str(e)}"
        )


@app.post("/api/v1/groups/{group_id}/members/remove")
async def remove_group_member(group_id: str, member_data: GroupMemberRemove):
    """移除群成员（退出群组）"""
    db = await get_db()
    
    try:
        await db.execute(
            """
            DELETE FROM group_members
            WHERE group_id = $1 AND user_id = $2
            """,
            group_id, member_data.user_id
        )
        
        return {"message": "已成功退出群组"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"操作失败：{str(e)}"
        )


@app.get("/api/v1/users/{user_id}/groups")
async def get_user_groups(user_id: str):
    """获取用户加入的群组列表"""
    db = await get_db()
    
    groups = await db.fetch(
        """
        SELECT g.id, g.name, g.description, g.owner_id, g.created_at,
               m.role as user_role
        FROM groups g
        JOIN group_members m ON g.id = m.group_id
        WHERE m.user_id = $1 AND g.status = 'active'
        ORDER BY g.created_at DESC
        """,
        user_id
    )
    
    return [dict(group) for group in groups]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
