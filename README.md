# 🦞 ClawChats - Phase 1 MVP

> 快速部署、能实际使用、能演示的通讯系统

---

## 🚀 快速开始

### 方式 1: Docker Compose (推荐)

```bash
cd claw-chats
docker-compose up -d

# 访问 http://localhost:8080
# Token: demo-token
```

### 方式 2: 本地开发

#### 启动数据库
```bash
docker run -d --name clawchats-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=clawchats \
  -p 5432:5432 \
  postgres:15-alpine
```

#### 启动服务器 (Python)
```bash
cd server
pip install -r requirements.txt
uvicorn main:app --reload --port 8765
```

#### 启动 Web
```bash
cd web
npm install
npm run dev  # Port: 5173
```

---

## 📦 组件说明

| 组件 | 端口 | 技术栈 | 说明 |
|------|------|--------|------|
| Message Server | 8765 | Python + FastAPI | WebSocket 消息服务 |
| Web Client | 8080 | Vue 3 + Vite | 用户聊天界面 |
| PostgreSQL | 5432 | PostgreSQL 15 | 数据库 |

---

## 🧪 测试

### Web 聊天测试
1. 打开两个浏览器窗口
2. 窗口 1: 用户 ID `user-1`, Token `demo-token`
3. 窗口 2: 用户 ID `user-2`, Token `demo-token`
4. 互相发送消息

### OpenClaw 集成测试
```json
{
  "channels": {
    "clawchats": {
      "enabled": true,
      "serverUrl": "ws://localhost:8765/ws",
      "userId": "openclaw-main",
      "token": "demo-token"
    }
  }
}
```

### API 测试
```bash
# 健康检查
curl http://localhost:8765/health

# 查看在线用户
curl http://localhost:8765/stats
```

---

## 📝 环境变量

### Message Server
| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PORT` | 8765 | WebSocket 端口 |
| `AUTH_TOKENS` | demo-token,test-token,admin-token | 认证 Token 列表（逗号分隔） |
| `DATABASE_URL` | postgresql://postgres:postgres@db:5432/clawchats | 数据库连接 |

---

## ✅ Phase 1 验收标准

- [x] Web 登录 - 输入 userId+token 能连接
- [x] Web→Web 消息 - 两个浏览器窗口能互相发消息
- [x] 消息持久化 - 重启服务器后消息不丢失
- [x] Docker 部署 - `docker-compose up` 后能访问
- [x] 在线状态 - 显示在线用户列表
- [x] 健康检查 API - `/health` 和 `/stats`

---

## 📁 项目结构

```
claw-chats/
├── server/              # WebSocket 服务器 (Python/FastAPI)
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── web/                 # Vue 3 Web 客户端
│   ├── src/
│   │   ├── App.vue
│   │   └── main.ts
│   ├── package.json
│   └── Dockerfile
├── channel/             # OpenClaw 插件 (TypeScript)
│   ├── src/
│   │   └── channel.ts
│   └── package.json
├── init-db/             # 数据库初始化
│   └── 01-init.sql
├── docker-compose.yml   # 一键部署
└── docs-proposals/      # 设计文档
```

---

## 🔧 开发命令

### Server (Python)
```bash
cd server
pip install -r requirements.txt
uvicorn main:app --reload    # 开发模式
python main.py               # 生产启动
```

### Web (Node.js)
```bash
cd web
npm install
npm run dev      # 开发模式 (Vite)
npm run build    # 构建
npm run preview  # 预览生产构建
```

### Channel (TypeScript)
```bash
cd channel
npm install
npm run dev      # 开发模式
npm run build    # 构建
```

---

## 📊 数据库表

- `users` - 用户表
- `user_sessions` - 在线状态
- `messages` - 消息记录

---

## 🔌 WebSocket 消息格式

### 认证
```json
{"type": "auth", "userId": "user-123", "token": "demo-token"}
{"type": "auth", "ok": true, "userId": "user-123"}
```

### 发送消息
```json
{"type": "message", "to": "user-456", "content": "你好"}
```

### 接收消息
```json
{
  "type": "message",
  "from": "user-123",
  "content": "你好",
  "timestamp": 1773130000000
}
```

### 在线状态
```json
{"type": "presence", "users": ["user-1", "user-2"], "timestamp": 1773130000000}
```

---

*Phase 1 MVP - 2026-03-11*
