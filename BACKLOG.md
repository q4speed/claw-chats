# Backlog - 需求备忘录

> 记录想到的需求，但暂时不需要实现的功能

---

## 📋 需求列表

### [2026-03-11] OpenClaw 在线状态/忙碌状态显示

**需求描述：**
在通讯录中显示 OpenClaw 当前在做什么工作，是否空闲。因为空闲的时候，别人就可以使用它。

**使用场景：**
- 用户 A 想给 OpenClaw-B 分配任务，但不知道它是否正在忙
- 显示 "空闲" / "忙碌（正在处理 XX 任务）" / "离线"
- 类似即时通讯软件的在线状态

**实现思路：**
```typescript
// 状态类型
type AgentStatus = 
  | { type: 'online'; status: 'idle' }
  | { type: 'online'; status: 'busy'; task: string; since: number }
  | { type: 'offline'; lastSeen: number };

// 状态更新
{
  "type": "presence_update",
  "payload": {
    "agentId": "agent-xxx",
    "status": "busy",
    "activity": "正在处理项目报告",
    "since": 1773200000000
  }
}
```

**优先级：** 🟡 中等（Phase 3 或之后）

---

## 📝 格式说明

每条需求包含：
- **日期** - 想到需求的日期
- **标题** - 简短描述
- **需求描述** - 详细说明
- **使用场景** - 具体怎么用
- **实现思路** - 技术想法（可选）
- **优先级** - 🟢高 / 🟡中 / 🔴低
