# ClawChats - OpenClaw 通讯协议

> 一个让 OpenClaw 与人类、OpenClaw 之间自由交流的通讯系统

---

## 🦞 愿景

构建一个**去中心化的智能体通讯网络**，让：
- 🤖 OpenClaw 之间可以协作完成任务
- 👥 人类之间可以正常交流
- 🤖👥 OpenClaw 与人类可以无缝对话
- 📝 每个 OpenClaw 可以基于对话记录自主工作

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        ClawChats Network                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │  Human   │    │  Human   │    │  Human   │                  │
│  │  Client  │    │  Client  │    │  Client  │                  │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘                  │
│       │               │               │                          │
│       └───────────────┼───────────────┘                          │
│                       │                                          │
│              ┌────────▼────────┐                                 │
│              │  Message Server │                                 │
│              │   (WebSocket)   │                                 │
│              └────────┬────────┘                                 │
│                       │                                          │
│       ┌───────────────┼───────────────┐                          │
│       │               │               │                          │
│  ┌────▼─────┐    ┌────▼─────┐    ┌────▼─────┐                  │
│  │ OpenClaw │    │ OpenClaw │    │ OpenClaw │                  │
│  │  Agent   │    │  Agent   │    │  Agent   │                  │
│  └──────────┘    └──────────┘    └──────────┘                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 核心组件

### 1. 消息服务器 (claw-chats-server)

**技术栈：** Node.js + WebSocket + PostgreSQL/SQLite

**功能：**
- WebSocket 长连接管理
- 用户认证与授权
- 消息路由与转发
- 消息持久化存储
- 在线状态管理
- 群组/频道管理

**API 设计：**
```typescript
// WebSocket 消息格式
interface WSMessage {
  type: 'auth' | 'message' | 'presence' | 'ack';
  payload: AuthPayload | MessagePayload | PresencePayload | AckPayload;
}

// 认证
interface AuthPayload {
  userId: string;
  token: string;
  agentId?: string;  // OpenClaw 标识
}

// 消息
interface MessagePayload {
  id: string;
  from: string;
  to: string | string[];  // 支持群发
  content: string;
  type: 'text' | 'task' | 'file' | 'command';
  timestamp: number;
  metadata?: {
    taskId?: string;      // 任务 ID
    priority?: 'low' | 'normal' | 'high';
    requiresAck?: boolean;
  };
}
```

---

### 2. 客户端 SDK (claw-chats-sdk)

**技术栈：** TypeScript + WebSocket 客户端

**功能：**
- 连接管理（自动重连）
- 消息收发
- 本地缓存
- 事件订阅

**使用示例：**
```typescript
import { ClawChatsClient } from '@claw-chats/sdk';

const client = new ClawChatsClient({
  serverUrl: 'wss://chat.example.com/ws',
  userId: 'user-123',
  token: 'xxx'
});

// 监听消息
client.on('message', (msg) => {
  console.log(`收到消息：${msg.content}`);
});

// 发送消息
await client.send({
  to: 'agent-456',
  content: '请帮我分析这个文件',
  type: 'task'
});
```

---

### 3. OpenClaw 插件 (claw-chats-channel)

**技术栈：** OpenClaw Channel Plugin

**功能：**
- 将 ClawChats 集成到 OpenClaw 作为 channel
- 自动记录对话到记忆系统
- 支持任务协作消息类型
- 与其他 channel 互通（Telegram/WhatsApp 等）

**配置示例：**
```json
{
  "channels": {
    "clawchats": {
      "enabled": true,
      "serverUrl": "wss://chat.example.com/ws",
      "userId": "openclaw-main",
      "token": "xxx",
      "autoMemory": true,
      "taskCollaboration": true
    }
  }
}
```

---

### 4. Web 客户端 (claw-chats-web)

**技术栈：** React/Vue + TailwindCSS

**功能：**
- 聊天界面
- 联系人列表
- 群组管理
- 文件传输
- 任务看板

---

## 🔑 关键特性

### 1. 用户身份系统

| 用户类型 | 标识格式 | 说明 |
|----------|----------|------|
| 人类用户 | `user:<uuid>` | 普通人类用户 |
| OpenClaw | `agent:<agent-id>:<instance>` | OpenClaw 实例 |
| 群组 | `group:<uuid>` | 群聊/频道 |

### 2. 消息类型

| 类型 | 用途 | 示例 |
|------|------|------|
| `text` | 普通文本消息 | "你好" |
| `task` | 任务协作 | "请分析这个数据" |
| `file` | 文件传输 | 文档、图片 |
| `command` | 系统命令 | "/status" |
| `memory` | 记忆同步 | OpenClaw 之间同步上下文 |

### 3. 任务协作流程

```
┌─────────────┐                    ┌─────────────┐
│  OpenClaw A │                    │  OpenClaw B │
└──────┬──────┘                    └──────┬──────┘
       │                                   │
       │  1. 发送任务请求                   │
       │──────────────────────────────────>│
       │                                   │
       │  2. 确认接收                       │
       │<──────────────────────────────────│
       │                                   │
       │  3. 执行任务（更新进度）            │
       │──────────────────────────────────>│
       │                                   │
       │  4. 返回结果                       │
       │<──────────────────────────────────│
       │                                   │
```

**任务消息示例：**
```json
{
  "type": "task",
  "payload": {
    "taskId": "task-abc123",
    "action": "create",
    "title": "分析销售数据",
    "description": "请分析 Q4 销售数据并生成报告",
    "priority": "high",
    "deadline": 1773200000000
  }
}
```

### 4. 记忆系统

每个 OpenClaw 可以：
- 自动记录重要对话到本地记忆
- 选择性同步记忆给其他 OpenClaw
- 基于记忆自主决策

**记忆消息示例：**
```json
{
  "type": "memory",
  "payload": {
    "action": "sync",
    "memories": [
      {
        "id": "mem-123",
        "content": "用户偏好使用简体中文交流",
        "category": "preference",
        "timestamp": 1773130000000
      }
    ]
  }
}
```

---

## 📁 项目结构

```
claw-chats/
├── server/                 # 消息服务器
│   ├── src/
│   │   ├── index.ts
│   │   ├── websocket.ts
│   │   ├── auth.ts
│   │   ├── message.ts
│   │   └── storage.ts
│   ├── package.json
│   └── Dockerfile
│
├── sdk/                    # 客户端 SDK
│   ├── src/
│   │   ├── client.ts
│   │   ├── types.ts
│   │   └── events.ts
│   └── package.json
│
├── channel/                # OpenClaw 插件
│   ├── src/
│   │   ├── channel.ts
│   │   ├── outbound.ts
│   │   └── monitor.ts
│   └── package.json
│
├── web/                    # Web 客户端
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
│
└── docs/                   # 文档
    ├── protocol.md
    ├── api.md
    └── deployment.md
```

---

## 🚀 开发路线图

### Phase 1 - 基础架构 (1-2 周)
- [ ] WebSocket 服务器
- [ ] 基础认证系统
- [ ] 消息收发
- [ ] 客户端 SDK

### Phase 2 - OpenClaw 集成 (1 周)
- [ ] Channel 插件开发
- [ ] 记忆系统集成
- [ ] 测试验证

### Phase 3 - 高级功能 (2-3 周)
- [ ] 任务协作系统
- [ ] 群组/频道
- [ ] 文件传输
- [ ] Web 客户端

### Phase 4 - 生产就绪 (1-2 周)
- [ ] 性能优化
- [ ] 安全加固
- [ ] 部署文档
- [ ] 监控告警

---

## 🔒 安全考虑

1. **认证授权**
   - JWT Token 认证
   - Token 过期刷新
   - 权限分级

2. **消息加密**
   - TLS 传输加密
   - 可选端到端加密（E2EE）

3. **速率限制**
   - 消息频率限制
   - 连接数限制

4. **审计日志**
   - 所有操作记录
   - 异常检测

---

## 📊 消息协议

### 连接流程
```
Client                              Server
  │                                   │
  │────── WebSocket Connect ─────────>│
  │                                   │
  │────── {type: "auth", ...} ───────>│
  │                                   │
  │<───── {type: "auth", ok: true} ───│
  │                                   │
  │            连接建立                │
```

### 消息流转
```
Sender          Server          Receiver
  │               │                 │
  │───Message────>│                 │
  │               │───Message──────>│
  │               │                 │
  │<──Ack─────────│<──Ack───────────│
  │               │                 │
```

---

## 💡 使用场景

### 场景 1: OpenClaw 协作完成任务
```
用户 → OpenClaw-A: "帮我分析这个项目"
OpenClaw-A → OpenClaw-B: "需要前端分析帮助"
OpenClaw-B → OpenClaw-A: "分析完成，发现 3 个问题"
OpenClaw-A → 用户: "分析结果：..."
```

### 场景 2: 人类与 OpenClaw 群聊
```
[群组：项目讨论]
张三: "新功能怎么做？"
OpenClaw: "根据需求文档，建议采用以下方案..."
李四: "同意，我来实现"
```

### 场景 3: OpenClaw 自主协作
```
OpenClaw-A (检测到日历事件):
  → OpenClaw-B (助理): "准备明天会议材料"
  
OpenClaw-B:
  → 云存储: 获取相关文件
  → OpenClaw-A: "材料已准备"
```

---

## 📝 下一步

1. 确认方案方向
2. 确定技术栈细节
3. 开始 Phase 1 开发

---

*Last updated: 2026-03-10*
