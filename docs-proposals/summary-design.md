# ClawChats - 概要设计文档

> 版本：1.0  
> 日期：2026-03-11  
> 状态：草稿

---

## 1. 文档概述

### 1.1 目的

本文档描述 ClawChats 系统的概要设计，包括系统架构、核心组件、服务划分、数据设计等。

### 1.2 范围

- 消息服务（Message Server）
- 后台管理服务（Admin Server）
- Web 客户端（用户聊天界面）
- 管理界面（Admin Web）
- OpenClaw Channel 插件
- 客户端 SDK

### 1.3 读者对象

- 开发团队
- 架构师
- 运维人员

---

## 2. 系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        ClawChats Network                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Web Client  │  │  Web Client  │  │  Web Client  │          │
│  │  (用户聊天)   │  │  (用户聊天)   │  │  (用户聊天)   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                    │
│         └─────────────────┼─────────────────┘                    │
│                           │                                      │
│                  ┌────────▼────────┐                             │
│                  │ Message Server  │                             │
│                  │  (WebSocket)    │                             │
│                  │  ★ 核心消息服务  │                             │
│                  └────────┬────────┘                             │
│                           │                                      │
│         ┌─────────────────┼─────────────────┐                    │
│         │                 │                 │                    │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐             │
│  │ OpenClaw-A  │  │ OpenClaw-B  │  │ OpenClaw-C  │             │
│  │  (Agent)    │  │  (Agent)    │  │  (Agent)    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Admin Server                            │  │
│  │                    (REST API)                              │  │
│  │                    ★ 后台管理服务                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                           │                                      │
│                  ┌────────▼────────┐                             │
│                  │   Admin Web     │                             │
│                  │   (管理界面)     │                             │
│                  └─────────────────┘                             │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    PostgreSQL                              │  │
│  │                    (共享数据库)                             │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 服务划分

| 服务 | 端口 | 协议 | 职责 | 独立性 |
|------|------|------|------|--------|
| **Message Server** | 8765 | WebSocket | 实时消息路由、连接管理 | 完全独立 |
| **Admin Server** | 8766 | HTTP/REST | 管理 API、配置管理 | 完全独立 |
| **Web Client** | 8080 | HTTP | 用户聊天界面 | 依赖 Message Server |
| **Admin Web** | 8081 | HTTP | 管理界面 | 依赖 Admin Server |

### 2.3 服务依赖关系

```
┌─────────────┐         ┌─────────────┐
│  Web Client │ ──────► │Message Server│
└─────────────┘         └─────────────┘

┌─────────────┐         ┌─────────────┐
│  Admin Web  │ ──────► │ Admin Server│
└─────────────┘         └─────────────┘

┌─────────────┐         ┌─────────────┐
│Message Server│ ──────►│ PostgreSQL  │
└─────────────┘         └─────────────┘

┌─────────────┐         ┌─────────────┐
│ Admin Server│ ──────►│ PostgreSQL  │
└─────────────┘         └─────────────┘
```

**关键设计原则：**
- ✅ Message Server 与 Admin Server **无直接依赖**
- ✅ 两者共享数据库，但运行时独立
- ✅ Admin Server 故障不影响消息收发
- ✅ Message Server 故障不影响管理查询

---

## 3. 核心组件设计

### 3.1 Message Server (消息服务器)

#### 3.1.1 职责
- WebSocket 长连接管理
- 用户认证与授权
- 消息路由与转发
- 消息持久化
- 在线状态管理
- 健康检查 API

#### 3.1.2 技术栈
- Python 3.11+
- FastAPI (WebSocket 支持)
- `asyncpg` (PostgreSQL 异步客户端)
- `uvicorn` (ASGI 服务器)

#### 3.1.3 核心模块

```
server/
├── main.py               # 主应用 (FastAPI + WebSocket)
├── requirements.txt      # Python 依赖
└── Dockerfile            # 容器化部署
```

#### 3.1.4 WebSocket 消息格式

```json
// 认证消息
{"type": "auth", "userId": "user-123", "token": "xxx", "agentId": "agent-xxx"}
{"type": "auth", "ok": true, "userId": "user-123"}

// 普通消息
{"type": "message", "to": "user-456", "content": "你好", "metadata": {}}

// 接收消息
{"type": "message", "from": "user-123", "content": "你好", "timestamp": 1773130000000}

// 在线状态
{"type": "presence", "users": ["user-1", "user-2"], "timestamp": 1773130000000}

// 心跳
{"type": "ping"} → {"type": "pong", "timestamp": 1773130000000}
```

#### 3.1.5 HTTP API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/stats` | GET | 在线用户统计 |
| `/ws` | WebSocket | 消息连接端点 |

---

### 3.2 Admin Server (后台管理服务器) - Phase 2

#### 3.2.1 职责
- 用户管理 API
- OpenClaw 实例管理
- 角色/身份分配
- 权限配置
- Token 管理
- 消息日志查询（只读）
- 系统监控

#### 3.2.2 技术栈
- Python 3.11+
- FastAPI
- `asyncpg` (PostgreSQL 异步客户端)
- `uvicorn` (ASGI 服务器)

#### 3.2.3 核心模块

```
admin-server/
├── main.py               # 主应用 (FastAPI)
├── api/                  # API 路由
│   ├── users.py          # 用户管理
│   ├── agents.py         # OpenClaw 管理
│   ├── roles.py          # 角色管理
│   ├── tokens.py         # Token 管理
│   └── logs.py           # 日志查询
├── models/               # 数据模型
├── services/             # 业务逻辑
│   ├── user_service.py
│   ├── role_service.py
│   └── audit_service.py
├── requirements.txt      # Python 依赖
└── Dockerfile            # 容器化部署
```

#### 3.2.4 API 设计

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/users` | GET/POST | 用户列表/创建 |
| `/api/v1/users/:id` | GET/DELETE | 用户详情/禁用 |
| `/api/v1/tokens` | GET/POST/DELETE | Token 管理 |
| `/api/v1/agents/:id/roles` | GET/POST/DELETE | 角色管理 |
| `/api/v1/messages` | GET | 消息日志查询 |
| `/api/v1/stats/overview` | GET | 系统统计 |

---

### 3.3 Web Client (用户聊天界面)

#### 3.3.1 职责
- 用户登录/认证
- 实时聊天界面
- 联系人列表
- 消息历史查看

#### 3.3.2 技术栈
- Vue 3 (Composition API)
- Vite
- Pinia
- Vue Router
- TailwindCSS

#### 3.3.3 核心组件

```
web/
├── src/
│   ├── App.vue
│   ├── main.ts
│   ├── components/
│   │   ├── ChatWindow.vue
│   │   ├── MessageList.vue
│   │   ├── MessageInput.vue
│   │   └── ContactList.vue
│   ├── views/
│   │   ├── Login.vue
│   │   └── Chat.vue
│   └── ws/
│       └── client.ts
```

---

### 3.4 Admin Web (后台管理界面)

#### 3.4.1 职责
- 用户管理界面
- OpenClaw 实例管理
- 角色分配/撤销
- 权限配置
- 系统监控面板

#### 3.4.2 技术栈
- Vue 3 (Composition API)
- Vite
- Pinia
- Vue Router
- Element Plus / Ant Design Vue

#### 3.4.3 核心模块

```
admin-web/
├── src/
│   ├── App.vue
│   ├── main.ts
│   ├── views/
│   │   ├── Dashboard.vue       # 仪表盘
│   │   ├── Users.vue           # 用户管理
│   │   ├── Agents.vue          # OpenClaw 管理
│   │   ├── Roles.vue           # 角色管理
│   │   ├── Permissions.vue     # 权限配置
│   │   ├── Logs.vue            # 日志查询
│   │   └── Settings.vue        # 系统设置
│   └── api/
│       └── client.ts           # API 客户端
```

#### 3.4.4 界面原型

**仪表盘：**
- 在线用户数
- 今日消息量
- OpenClaw 实例状态
- 系统健康度

**用户管理：**
- 用户列表（表格）
- 创建用户（表单）
- 禁用/启用用户
- Token 生成/撤销

**角色管理：**
- OpenClaw 实例列表
- 当前角色显示
- 角色分配（下拉选择）
- 角色撤销

---

### 3.5 OpenClaw Channel 插件

#### 3.5.1 职责
- 连接 Message Server
- 收发消息
- 角色消息处理
- 本地记忆更新

#### 3.5.2 核心模块

```
channel/
├── src/
│   ├── channel.ts          # Channel 主逻辑
│   ├── outbound.ts         # 消息发送
│   ├── monitor.ts          # 消息监听
│   └── memory.ts           # 记忆集成
```

---

### 3.6 Client SDK - Phase 2

#### 3.6.1 职责
- WebSocket 连接封装
- 自动重连
- 消息收发 API
- 事件订阅

#### 3.6.2 技术栈
- Python (优先)
- TypeScript (可选)

#### 3.6.3 使用示例 (Python)

```python
from claw_chats import ClawChatsClient

client = ClawChatsClient(
    server_url='ws://localhost:8765/ws',
    user_id='user-123',
    token='xxx'
)

# 监听消息
@client.on('message')
def handle_message(msg):
    print(f"收到消息：{msg['content']}")

# 发送消息
await client.send(to='agent-456', content='请帮我分析这个文件')
```

---

## 4. 数据设计

### 4.1 数据库表结构

#### 4.1.1 用户表

```sql
CREATE TABLE users (
  id VARCHAR(64) PRIMARY KEY,
  name VARCHAR(128),
  email VARCHAR(255),
  status VARCHAR(32) DEFAULT 'active',  -- active | disabled
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_status ON users(status);
```

#### 4.1.2 用户会话表（在线状态）

```sql
CREATE TABLE user_sessions (
  user_id VARCHAR(64) PRIMARY KEY REFERENCES users(id),
  connected_at TIMESTAMP NOT NULL,
  disconnected_at TIMESTAMP,
  last_seen_at TIMESTAMP
);

CREATE INDEX idx_sessions_connected ON user_sessions(connected_at);
```

#### 4.1.3 消息表

```sql
CREATE TABLE messages (
  id BIGSERIAL PRIMARY KEY,
  from_user VARCHAR(64) REFERENCES users(id),
  to_user VARCHAR(64) REFERENCES users(id),
  content TEXT NOT NULL,
  message_type VARCHAR(32) DEFAULT 'text',  -- text | task | file | role
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_messages_to_user ON messages(to_user);
CREATE INDEX idx_messages_from_user ON messages(from_user);
CREATE INDEX idx_messages_created ON messages(created_at);
```

#### 4.1.4 Token 表

```sql
CREATE TABLE tokens (
  id VARCHAR(64) PRIMARY KEY,
  user_id VARCHAR(64) REFERENCES users(id),
  name VARCHAR(128),
  expires_at TIMESTAMP,
  revoked_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tokens_user ON tokens(user_id);
CREATE INDEX idx_tokens_expires ON tokens(expires_at);
```

#### 4.1.5 角色表

```sql
CREATE TABLE agent_roles (
  id SERIAL PRIMARY KEY,
  agent_id VARCHAR(64) NOT NULL,
  owner_id VARCHAR(64) NOT NULL,
  role_name VARCHAR(128) NOT NULL,
  role_description TEXT,
  permissions JSONB,
  metadata JSONB,
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP,
  revoked_at TIMESTAMP,
  revoked_reason TEXT
);

CREATE INDEX idx_agent_roles_agent ON agent_roles(agent_id);
CREATE INDEX idx_agent_roles_active ON agent_roles(agent_id, active);
```

#### 4.1.6 OpenClaw 实例表

```sql
CREATE TABLE agents (
  id VARCHAR(64) PRIMARY KEY,
  owner_id VARCHAR(64) REFERENCES users(id),
  name VARCHAR(128),
  status VARCHAR(32) DEFAULT 'active',  -- active | disabled
  last_seen_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_agents_owner ON agents(owner_id);
CREATE INDEX idx_agents_status ON agents(status);
```

---

## 5. 部署架构

### 5.1 Docker Compose 部署

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: clawchats
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-db:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  # 核心消息服务 (Python/FastAPI)
  message-server:
    build: ./server
    ports:
      - "8765:8765"
    environment:
      - PORT=8765
      - AUTH_TOKENS=demo-token,test-token,admin-token
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/clawchats
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  # 后台管理服务（独立部署）
  admin-server:
    build: ./admin-server
    ports:
      - "8766:8766"
    environment:
      - PORT=8766
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/clawchats
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  # 用户聊天界面
  web-client:
    build: ./web
    ports:
      - "8080:80"
    depends_on:
      - message-server
    restart: unless-stopped

  # 后台管理界面（独立部署）
  admin-web:
    build: ./admin-web
    ports:
      - "8081:80"
    depends_on:
      - admin-server
    restart: unless-stopped

volumes:
  postgres_data:
```

### 5.2 服务独立性说明

| 场景 | Message Server | Admin Server | 影响 |
|------|---------------|--------------|------|
| Admin Server 宕机 | ✅ 正常运行 | ❌ 停止 | 管理功能不可用，消息收发正常 |
| Message Server 宕机 | ❌ 停止 | ✅ 正常运行 | 消息中断，管理查询正常 |
| Admin Web 宕机 | ✅ 正常运行 | ✅ 正常运行 | 仅管理界面不可访问 |
| Web Client 宕机 | ✅ 正常运行 | ✅ 正常运行 | 仅用户聊天界面不可访问 |
| PostgreSQL 宕机 | ❌ 停止 | ❌ 停止 | 全系统不可用 |

---

## 6. 安全设计

### 6.1 认证机制

- **Message Server:** Token 预共享认证
- **Admin Server:** JWT Token 认证

### 6.2 权限控制

| 操作 | 权限要求 |
|------|----------|
| 发送消息 | 有效 Token |
| 创建用户 | Admin Token |
| 分配角色 | Admin Token + Owner 权限 |
| 查询日志 | Admin Token |
| 撤销 Token | Admin Token |

### 6.3 传输安全

- 生产环境强制使用 TLS (wss:// + https://)
- 内部服务通信使用内网

---

## 7. 开发计划

### Phase 1 (MVP) - 1 周
- Message Server 基础功能
- Web Client 基础聊天
- OpenClaw Channel 插件
- Docker 一键部署

### Phase 2 - 2 周
- Admin Server 基础 API
- Admin Web 基础界面
- 角色系统
- 消息持久化

### Phase 3 - 2 周
- 权限系统完善
- 任务审查流程
- 日志查询增强

### Phase 4 - 1-2 周
- 性能优化
- 监控告警
- 生产部署

---

## 8. 附录

### 8.1 术语表

| 术语 | 说明 |
|------|------|
| Message Server | 核心消息服务，处理 WebSocket 连接 |
| Admin Server | 后台管理服务，提供管理 API |
| OpenClaw | 智能体实例 |
| Channel | OpenClaw 通讯插件 |

### 8.2 参考文档

- [总体设计](overall-plan.md)
- [Phase 1 MVP 实现](../../README.md)
- [角色系统设计](./role-system.md)

### 8.3 技术栈总结

| 组件 | 技术栈 |
|------|--------|
| Message Server | Python 3.11 + FastAPI + asyncpg |
| Admin Server | Python 3.11 + FastAPI + asyncpg |
| Web Client | Vue 3 + Vite + TailwindCSS |
| Channel 插件 | TypeScript + ws |
| 数据库 | PostgreSQL 15 |
| 部署 | Docker + Docker Compose |
