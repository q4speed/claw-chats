# Phase 1 - MVP 详细设计

> 目标：1 周内完成，能快速部署、能实际使用、能演示

---

## 📦 Phase 1 功能范围

### ✅ 包含的功能
| 功能 | 说明 |
|------|------|
| 用户注册/登录 | 简易 Token 认证 |
| 一对一聊天 | 文字消息收发 |
| OpenClaw 接入 | Channel 插件 |
| Web 界面 | Vue 3 单页应用 |
| Docker 部署 | 一键启动 |

### ❌ 暂不包含
- 群组聊天
- 文件传输
- 任务系统
- 复杂权限
- 消息持久化（内存存储）

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
│  │  (WebSocket)    │    │  (Vue 3 + Nginx)│            │
│  │  Port: 8765     │    │  Port: 8080     │            │
│  └─────────────────┘    └─────────────────┘            │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 项目结构

```
claw-chats/
├── server/                 # WebSocket 服务器
│   ├── src/
│   │   └── index.ts        # 单文件服务器
│   ├── package.json
│   └── Dockerfile
│
├── web/                    # Vue 3 Web 客户端
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.ts
│   │   └── ws.ts           # WebSocket 客户端
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
│
├── channel/                # OpenClaw 插件
│   ├── src/
│   │   ├── channel.ts
│   │   ├── outbound.ts
│   │   └── monitor.ts
│   └── package.json
│
├── docker-compose.yml      # 一键部署
└── docs/
    └── phase1-mvp.md
```

---

## 🔧 服务器设计 (server/)

### 技术栈
- Node.js 20+
- `ws` (WebSocket)
- `express` (可选，用于健康检查)
- TypeScript

### 核心功能

```typescript
// server/src/index.ts
import { WebSocketServer, WebSocket } from 'ws';

const PORT = process.env.PORT || 8765;
const AUTH_TOKENS = new Set(process.env.AUTH_TOKENS?.split(',') || ['demo-token']);

// 存储在线用户
const users = new Map<string, WebSocket>();

const wss = new WebSocketServer({ port: PORT });

wss.on('connection', (ws, req) => {
  let userId: string | null = null;
  
  // 认证
  ws.on('message', (data) => {
    const msg = JSON.parse(data.toString());
    
    if (msg.type === 'auth') {
      if (AUTH_TOKENS.has(msg.token)) {
        userId = msg.userId;
        users.set(userId, ws);
        ws.send(JSON.stringify({ type: 'auth', ok: true }));
      } else {
        ws.send(JSON.stringify({ type: 'auth', ok: false, error: 'Invalid token' }));
        ws.close();
      }
      return;
    }
    
    // 转发消息
    if (msg.type === 'message' && userId) {
      const target = users.get(msg.to);
      if (target) {
        target.send(JSON.stringify({
          type: 'message',
          from: userId,
          content: msg.content,
          timestamp: Date.now()
        }));
      }
    }
  });
  
  ws.on('close', () => {
    if (userId) users.delete(userId);
  });
});

console.log(`Server running on port ${PORT}`);
```

### 消息格式

```typescript
// 认证
{ "type": "auth", "userId": "user-123", "token": "xxx" }
{ "type": "auth", "ok": true }

// 发送消息
{ "type": "message", "to": "user-456", "content": "你好" }

// 接收消息
{ "type": "message", "from": "user-123", "content": "你好", "timestamp": 1773130000000 }
```

---

## 🌐 Web 客户端设计 (web/)

### 技术栈
- Vue 3 (Composition API)
- Vite
- TailwindCSS

### 核心组件

```vue
<!-- web/src/App.vue -->
<template>
  <div class="chat-container">
    <!-- 登录界面 -->
    <div v-if="!connected" class="login">
      <input v-model="userId" placeholder="用户 ID" />
      <input v-model="token" type="password" placeholder="Token" />
      <button @click="connect">连接</button>
    </div>
    
    <!-- 聊天界面 -->
    <div v-else class="chat">
      <div class="messages">
        <div v-for="msg in messages" :key="msg.timestamp">
          <strong>{{ msg.from }}:</strong> {{ msg.content }}
        </div>
      </div>
      <div class="input">
        <input v-model="newMessage" @keyup.enter="send" />
        <button @click="send">发送</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useWebSocket } from './ws';

const userId = ref('');
const token = ref('');
const connected = ref(false);
const messages = ref([]);
const newMessage = ref('');

const { connect: wsConnect, send: wsSend } = useWebSocket();

const connect = () => {
  wsConnect('ws://localhost:8765', { userId: userId.value, token: token.value });
  wsConnect.on('message', (msg) => messages.value.push(msg));
  connected.value = true;
};

const send = () => {
  wsSend({ type: 'message', to: 'broadcast', content: newMessage.value });
  newMessage.value = '';
};
</script>
```

---

## 🦞 OpenClaw Channel 插件 (channel/)

### 配置示例

```json
{
  "channels": {
    "clawchats": {
      "enabled": true,
      "serverUrl": "ws://localhost:8765",
      "userId": "openclaw-main",
      "token": "demo-token"
    }
  }
}
```

### 核心代码

```typescript
// channel/src/monitor.ts
import WebSocket from 'ws';

export async function monitorClawChats({ config, runtime }) {
  const ws = new WebSocket(config.serverUrl);
  
  ws.on('open', () => {
    ws.send(JSON.stringify({
      type: 'auth',
      userId: config.userId,
      token: config.token
    }));
  });
  
  ws.on('message', (data) => {
    const msg = JSON.parse(data.toString());
    if (msg.type === 'message') {
      runtime?.handleInbound?.({
        channelId: 'clawchats',
        peerId: msg.from,
        text: msg.content,
        timestamp: msg.timestamp
      });
    }
  });
}

// channel/src/outbound.ts
export const outbound = {
  async sendText({ cfg, to, text, accountId }) {
    // 发送消息到 WebSocket
    return { ok: true };
  }
};
```

---

## 🐳 Docker 部署

### docker-compose.yml

```yaml
version: '3.8'

services:
  server:
    build: ./server
    ports:
      - "8765:8765"
    environment:
      - PORT=8765
      - AUTH_TOKENS=demo-token,test-token
    restart: unless-stopped

  web:
    build: ./web
    ports:
      - "8080:80"
    depends_on:
      - server
    restart: unless-stopped
```

### Dockerfile (server)

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
CMD ["node", "dist/index.js"]
```

### Dockerfile (web)

```dockerfile
# Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Serve
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

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

```bash
# 启动服务器
cd server
npm install
npm run dev  # Port: 8765

# 启动 Web
cd web
npm install
npm run dev  # Port: 5173 (Vite)
```

### 方式 3: OpenClaw 集成

```bash
# 安装插件
openclaw plugins install /path/to/claw-chats/channel

# 配置
# 编辑 ~/.openclaw/openclaw.json
{
  "channels": {
    "clawchats": {
      "enabled": true,
      "serverUrl": "ws://localhost:8765",
      "userId": "openclaw-main",
      "token": "demo-token"
    }
  }
}

# 重启 Gateway
openclaw gateway restart
```

---

## ✅ Phase 1 验收标准

| 测试项 | 预期结果 |
|--------|----------|
| Web 登录 | 输入 userId+token 能连接 |
| Web→Web 消息 | 两个浏览器窗口能互相发消息 |
| Web→OpenClaw 消息 | Web 发送，OpenClaw 能收到 |
| OpenClaw→Web 消息 | OpenClaw 发送，Web 能收到 |
| Docker 部署 | `docker-compose up` 后能访问 |
| 断线重连 | 网络恢复后自动重连 |

---

## 📝 下一步

1. 确认 Phase 1 设计
2. 开始编码实现
3. 测试验证
4. 演示准备
