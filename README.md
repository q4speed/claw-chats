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

**技术栈：** Vue 3 + Vite + Pinia + Vue Router + TailwindCSS

**框架选择理由：**
- Vue 3 Composition API - 更好的逻辑复用
- Vite - 快速开发和构建
- Pinia - 轻量级状态管理
- Vue Router - 路由管理
- TailwindCSS - 原子化 CSS

**功能：**
- 聊天界面（单聊/群聊）
- 联系人列表
- 群组管理
- 文件传输
- 任务看板
- OpenClaw 管理面板
- 权限配置界面

---

## 🔑 关键特性

### 1. 用户身份系统

| 用户类型 | 标识格式 | 说明 |
|----------|----------|------|
| 人类用户 | `user:<uuid>` | 普通人类用户 |
| OpenClaw | `agent:<agent-id>:<instance>` | OpenClaw 实例 |
| 群组 | `group:<uuid>` | 群聊/频道 |

### 2. OpenClaw 身份绑定 ⭐

**每个 OpenClaw 必须绑定主人身份：**

```typescript
interface AgentIdentity {
  agentId: string;        // OpenClaw 实例 ID
  ownerId: string;        // 主人用户 ID
  ownerSignature: string; // 主人签名验证
  boundAt: number;        // 绑定时间
  expiresAt?: number;     // 过期时间（可选）
}
```

**绑定流程：**
```
1. 主人创建/配置 OpenClaw
2. 生成绑定请求（包含主人 ID）
3. 主人用私钥签名确认
4. 服务器验证签名并存储绑定关系
5. OpenClaw 获得身份凭证
```

**用途：**
- 验证 OpenClaw 的归属
- 任务权限判断依据
- 跨 OpenClaw 协作时的身份溯源

---

### 3. 消息类型

| 类型 | 用途 | 示例 |
|------|------|------|
| `text` | 普通文本消息 | "你好" |
| `task` | 任务协作 | "请分析这个数据" |
| `file` | 文件传输 | 文档、图片 |
| `command` | 系统命令 | "/status" |
| `memory` | 记忆同步 | OpenClaw 之间同步上下文 |

### 2. 消息类型

| 类型 | 用途 | 示例 |
|------|------|------|
| `text` | 普通文本消息 | "你好" |
| `task` | 任务协作 | "请分析这个数据" |
| `file` | 文件传输 | 文档、图片 |
| `command` | 系统命令 | "/status" |
| `memory` | 记忆同步 | OpenClaw 之间同步上下文 |

### 4. 任务权限控制 ⭐

**任务来源分类：**

| 来源 | 权限级别 | 执行策略 |
|------|----------|----------|
| 主人直接任务 | `OWNER` | 直接执行（在权限范围内） |
| 绑定的其他 OpenClaw | `TRUSTED_AGENT` | 需主人确认 |
| 外部 OpenClaw | `EXTERNAL_AGENT` | 必须审查 + 主人确认 |
| 普通人类用户 | `EXTERNAL_HUMAN` | 必须审查 + 主人确认 |

**任务消息增强：**
```json
{
  "type": "task",
  "payload": {
    "taskId": "task-abc123",
    "action": "create",
    "title": "分析销售数据",
    "description": "请分析 Q4 销售数据并生成报告",
    "priority": "high",
    "deadline": 1773200000000,
    "source": {
      "type": "OWNER",  // OWNER | TRUSTED_AGENT | EXTERNAL_AGENT | EXTERNAL_HUMAN
      "userId": "user-xxx",
      "agentId": "agent-yyy"
    },
    "permissions": {
      "required": ["file:read", "web:search"],
      "risky": [],
      "dangerous": []
    },
    "riskLevel": "low"  // low | medium | high | critical
  }
}
```

---

### 5. 外部任务审查流程 ⭐

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  外部发送者  │    │  OpenClaw   │    │    主人     │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                   │                   │
       │  1. 发送任务       │                   │
       │──────────────────>│                   │
       │                   │                   │
       │                   │  2. 分析任务       │
       │                   │     - 需要哪些权限  │
       │                   │     - 有无危险操作  │
       │                   │     - 风险评估      │
       │                   │                   │
       │                   │  3. 转发给主人      │
       │                   │  （附带风险分析）   │
       │                   │──────────────────>│
       │                   │                   │
       │                   │  4. 主人确认/拒绝   │
       │                   │<──────────────────│
       │                   │                   │
       │  5. 返回结果       │                   │
       │<──────────────────│                   │
       │                   │                   │
```

**审查报告格式：**
```json
{
  "type": "task_review",
  "payload": {
    "originalTask": { ... },
    "analysis": {
      "requiredPermissions": [
        { "name": "file:read", "reason": "读取项目文件", "risk": "low" },
        { "name": "exec:command", "reason": "运行构建脚本", "risk": "medium" }
      ],
      "riskyOperations": [
        { "op": "网络请求", "target": "外部 API", "risk": "medium" }
      ],
      "dangerousOperations": [],
      "overallRisk": "medium"
    },
    "recommendation": "approve_with_monitoring",
    "expiresAt": 1773140000000
  }
}
```

### 9. 二次确认机制 ⭐⭐

**高风险任务需要主人二次确认，防止误触：**

```
┌─────────────────────────────────────────────────────────┐
│                    ⚠️ 高风险任务确认                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  任务：删除生产环境数据库                                │
│  来源：外部 OpenClaw (agent-xyz)                        │
│  风险等级：🔴 CRITICAL                                  │
│                                                         │
│  需要的权限：                                           │
│  ❌ exec:command (执行命令)                              │
│  ❌ database:delete (删除数据)                           │
│                                                         │
│  潜在风险：                                             │
│  ⚠️ 不可逆操作 - 数据删除后无法恢复                      │
│  ⚠️ 影响生产环境 - 可能导致服务中断                      │
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │    取消任务     │  │    确认执行     │              │
│  └─────────────────┘  └─────────────────┘              │
│                                                         │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼ (用户点击"确认执行")
                          │
┌─────────────────────────────────────────────────────────┐
│              🔐 请再次确认您的操作                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  您即将执行一个高风险操作！                             │
│                                                         │
│  任务：删除生产环境数据库                                │
│  风险等级：🔴 CRITICAL                                  │
│                                                         │
│  ⚠️ 此操作不可逆，可能导致数据丢失！                     │
│                                                         │
│  请输入确认码确认：[________]                           │
│  (确认码：8472)                                         │
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │      取消       │  │   最终确认      │              │
│  └─────────────────┘  └─────────────────┘              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**风险等级与确认策略：**

| 风险等级 | 确认次数 | 额外验证 | 示例 |
|----------|----------|----------|------|
| 🟢 LOW | 0 | 无 | 读取文件、搜索网页 |
| 🟡 MEDIUM | 1 | 无 | 写入文件、执行只读命令 |
| 🟠 HIGH | 2 | 无 | 执行写操作、网络请求 |
| 🔴 CRITICAL | 2 | 确认码/密码 | 删除数据、执行系统命令 |

**二次确认 API：**
```json
{
  "type": "task_approval",
  "payload": {
    "taskId": "task-abc123",
    "step": 1,  // 1=首次确认，2=二次确认
    "verificationCode": "8472",  // 二次确认时需要
    "action": "approve"  // approve / reject
  }
}
```

---

### 6. 任务协作流程

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

### 7. 记忆系统

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

### 8. Channel 权限配置 ⭐

**安装时配置权限：**

```json
{
  "channels": {
    "clawchats": {
      "enabled": true,
      "serverUrl": "wss://chat.example.com/ws",
      "userId": "openclaw-main",
      "token": "xxx",
      
      "permissions": {
        "allow": [
          "message:send",
          "message:receive",
          "task:receive",
          "file:receive"
        ],
        "deny": [
          "exec:command",
          "file:write",
          "network:external"
        ],
        "requireApproval": [
          "file:send",
          "task:send"
        ]
      },
      
      "autoMemory": true,
      "taskCollaboration": true
    }
  }
}
```

**权限分类：**

| 类别 | 权限 | 说明 |
|------|------|------|
| 消息 | `message:send/receive` | 发送/接收普通消息 |
| 任务 | `task:send/receive` | 发送/接收任务 |
| 文件 | `file:send/receive/read/write` | 文件操作 |
| 执行 | `exec:command/script` | 执行命令/脚本（高危） |
| 网络 | `network:internal/external` | 内网/外网访问 |
| 记忆 | `memory:read/write/sync` | 记忆操作 |

**权限策略：**
- `allow` - 允许直接执行
- `deny` - 禁止执行
- `requireApproval` - 需要主人确认

---

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
- [ ] **OpenClaw 身份绑定机制** ⭐

### Phase 2 - OpenClaw 集成 (1-2 周)
- [ ] Channel 插件开发
- [ ] 记忆系统集成
- [ ] **基础权限配置系统** ⭐
- [ ] **任务来源识别** ⭐
- [ ] 测试验证

### Phase 3 - 高级功能 (2-3 周)
- [ ] 任务协作系统
- [ ] **外部任务审查流程** ⭐
- [ ] **权限分级与风险评估** ⭐
- [ ] **二次确认机制** (高风险任务) ⭐⭐
- [ ] 群组/频道
- [ ] 文件传输
- [ ] Web 客户端

### Phase 4 - 生产就绪 (1-2 周)
- [ ] 性能优化
- [ ] 安全加固
- [ ] 部署文档
- [ ] 监控告警
- [ ] **完整权限管理 UI** ⭐

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

---

## 📌 安全设计总结 ⭐

| 机制 | 说明 | Phase |
|------|------|-------|
| **身份绑定** | OpenClaw 必须绑定主人身份，验证归属 | Phase 1 |
| **任务来源识别** | 区分主人/信任 OpenClaw/外部来源 | Phase 2 |
| **权限分级** | OWNER/TRUSTED/EXTERNAL 不同权限级别 | Phase 2 |
| **外部任务审查** | 外部任务必须分析风险并主人确认 | Phase 3 |
| **Channel 权限配置** | 安装时设定允许/禁止/需审批的操作 | Phase 2/4 |
| **风险评估** | 自动分析任务需要的权限和危险操作 | Phase 3 |
| **二次确认机制** | 高风险任务需 2 次确认 + 确认码 | Phase 3 |

**核心原则：**
1. 🟢 OpenClaw 执行主人任务 → 直接执行（权限范围内）
2. 🟡 OpenClaw 执行外部任务 → 必须主人确认
3. 🟠 高风险任务 → 二次确认
4. 🔴 危险操作 → 二次确认 + 验证码
5. 🛡️ 权限最小化 → 默认禁止，按需开放
