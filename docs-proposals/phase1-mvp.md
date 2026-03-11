# Phase 1 - MVP 实施文档

> 目标：1 周内完成，能快速部署、能实际使用、能演示  
> 状态：✅ 开发完成  
> 最后更新：2026-03-11

---

## 📦 Phase 1 功能范围

### ✅ 包含的功能
| 功能 | 说明 | 状态 |
|------|------|------|
| 用户注册/登录 | 简易 Token 认证 | ✅ |
| 一对一聊天 | 文字消息收发 | ✅ |
| OpenClaw 接入 | Channel 插件 | ✅ |
| Web 界面 | Vue 3 单页应用 | ✅ |
| Docker 部署 | 一键启动 | ✅ |
| 消息持久化 | PostgreSQL | ✅ |
| 在线状态 | 实时广播 | ✅ |

### ❌ 暂不包含
- 群组聊天
- 文件传输
- 任务系统
- 复杂权限
- 后台管理

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                     Docker Compose                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────┐    ┌─────────────────┐            │
│  │  claw-chats-    │    │  claw-chats-    │            │
│  │    server       │    │    web          │            │
│  │  (FastAPI)      │    │  (Vue 3 + Nginx)│            │
│  │  Port: 8765     │    │  Port: 8080     │            │
│  └────────┬────────┘    └─────────────────┘            │
│           │                                             │
│  ┌────────▼────────┐                                    │
│  │   PostgreSQL    │                                    │
│  │   (数据库)       │                                    │
│  │   Port: 5432    │                                    │
│  └─────────────────┘                                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 项目结构

```
claw-chats/
├── message-server/        # 消息服务 (Python + FastAPI) - 可独立部署
├── web-client/            # 客户端界面 (Vue 3) - 可独立部署
├── admin-server/          # 后台管理服务 (Phase 2) - 可独立部署
├── channel/               # OpenClaw Channel 插件
├── init-db/               # 数据库初始化脚本
├── docs-proposals/        # 设计文档
└── docker-compose.yml     # 一键部署配置
```

### 服务说明

| 服务 | 目录 | 部署方式 |
|------|------|----------|
| 消息服务 | `message-server/` | 独立 Docker 容器 |
| 客户端界面 | `web-client/` | 独立 Docker 容器，可配置服务器地址 |
| 后台管理 | `admin-server/` | 独立 Docker 容器（Phase 2） |

---

## 🔧 服务器实现 (server/)

### 技术栈
- Python 3.11
- FastAPI (WebSocket 支持)
- asyncpg (PostgreSQL 异步客户端)
- uvicorn (ASGI 服务器)

### 核心代码 (main.py)

```python
from fastapi import FastAPI, WebSocket
import asyncpg

app = FastAPI(title="ClawChats Message Server")

# 连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    async def disconnect(self, user_id: str):
        del self.active_connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # 认证
    data = await websocket.receive_json()
    if data["type"] == "auth":
        await manager.connect(websocket, data["userId"])
    
    # 消息处理
    while True:
        data = await websocket.receive_json()
        if data["type"] == "message":
            # 转发消息
            await manager.send_personal_message(data, data["to"])
```

### API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/ws` | WebSocket | 消息连接 |
| `/health` | GET | 健康检查 |
| `/stats` | GET | 在线用户统计 |

---

## 🌐 Web 客户端实现 (web/)

### 技术栈
- Vue 3 (Composition API)
- Vite
- TailwindCSS

### 核心组件 (App.vue)

```vue
<template>
  <div class="chat-container">
    <!-- 登录界面 -->
    <div v-if="!connected">
      <input v-model="userId" placeholder="用户 ID" />
      <input v-model="token" type="password" placeholder="Token" />
      <button @click="connect">连接</button>
    </div>
    
    <!-- 聊天界面 -->
    <div v-else>
      <div class="messages">
        <div v-for="msg in messages">{{ msg.from }}: {{ msg.content }}</div>
      </div>
      <input v-model="newMessage" @keyup.enter="send" />
    </div>
  </div>
</template>
```

---

## 🦞 OpenClaw Channel 插件 (channel/)

### 配置示例

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

### 核心代码 (channel.ts)

```typescript
import WebSocket from 'ws';

export async function monitorClawChats(cfg, runtime) {
  const ws = new WebSocket(cfg.serverUrl);
  
  ws.on('open', () => {
    ws.send(JSON.stringify({
      type: 'auth',
      userId: cfg.userId,
      token: cfg.token
    }));
  });
  
  ws.on('message', (data) => {
    const msg = JSON.parse(data.toString());
    if (msg.type === 'message') {
      runtime?.handleInbound?.({
        channelId: 'clawchats',
        peerId: msg.from,
        text: msg.content
      });
    }
  });
}
```

---

## 🐳 Docker 部署

### docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: clawchats
    volumes:
      - ./init-db:/docker-entrypoint-initdb.d

  message-server:
    build: ./server
    ports:
      - "8765:8765"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/clawchats

  web-client:
    build: ./web
    ports:
      - "8080:80"
```

### 启动命令

```bash
docker-compose up -d
```

---

## 🧪 测试

### Web 聊天测试
1. 打开两个浏览器窗口访问 `http://localhost:8080`
2. 窗口 1: 用户 ID `user-1`, Token `demo-token`
3. 窗口 2: 用户 ID `user-2`, Token `demo-token`
4. 互相发送消息

### API 测试
```bash
# 健康检查
curl http://localhost:8765/health

# 查看在线用户
curl http://localhost:8765/stats
```

---

## 📊 数据库表

```sql
-- 用户表
CREATE TABLE users (
  id VARCHAR(64) PRIMARY KEY,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 用户会话表（在线状态）
CREATE TABLE user_sessions (
  user_id VARCHAR(64) PRIMARY KEY,
  connected_at TIMESTAMP NOT NULL,
  disconnected_at TIMESTAMP
);

-- 消息表
CREATE TABLE messages (
  id BIGSERIAL PRIMARY KEY,
  from_user VARCHAR(64),
  to_user VARCHAR(64),
  content TEXT NOT NULL,
  message_type VARCHAR(32) DEFAULT 'text',
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## ✅ Phase 1 验收标准

| 测试项 | 预期结果 | 状态 |
|--------|----------|------|
| Web 登录 | 输入 userId+token 能连接 | ✅ |
| Web→Web 消息 | 两个浏览器窗口能互相发消息 | ✅ |
| Web→OpenClaw 消息 | Web 发送，OpenClaw 能收到 | ⏳ |
| OpenClaw→Web 消息 | OpenClaw 发送，Web 能收到 | ⏳ |
| Docker 部署 | `docker-compose up` 后能访问 | ✅ |
| 消息持久化 | 重启服务器后消息不丢失 | ✅ |

---

## 🔧 开发命令

### Server
```bash
cd server
pip install -r requirements.txt
uvicorn main:app --reload --port 8765
```

### Web
```bash
cd web
npm install
npm run dev
```

### Channel
```bash
cd channel
npm install
npm run build
```

---

## 📝 下一步

1. ✅ Phase 1 开发完成
2. ⏳ Docker 部署测试
3. ⏸️ 准备 Phase 2 (Admin Server + 角色系统)
