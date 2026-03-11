# OpenClaw 身份/角色系统设计

> 如何让 OpenClaw 长期扮演某个角色（如项目经理），直到取消为止

---

## 🎯 问题本质

**需求：**
- 主人对 OpenClaw-A 说："你是项目经理，负责项目管理"
- OpenClaw-A 需要**长期记住**这个身份
- 在职责范围内**主动行动**（汇报、回复）
- 直到主人**取消身份**为止

**关键点：**
1. 身份需要**持久化存储**
2. 身份影响 OpenClaw 的**行为决策**
3. 身份需要可**查询、可取消**
4. 其他 OpenClaw/人类可能需要**知道**这个角色

---

## 🏗️ 设计方案

### 方案对比

| 方案 | 存储位置 | 优点 | 缺点 |
|------|----------|------|------|
| A. OpenClaw 本地记忆 | MEMORY.md | 直接读取，自主执行 | 其他方不知道 |
| B. 通讯服务器 | PostgreSQL | 集中管理，可同步 | OpenClaw 需查询 |
| C. Channel 配置 | openclaw.json | 配置化 | 不灵活 |
| **D. 混合方案** ⭐ | **两者结合** | **兼顾自主性和可见性** | **实现稍复杂** |

---

## ✅ 推荐方案：混合架构

```
┌─────────────────────────────────────────────────────────────┐
│                      身份/角色系统                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │  主人用户    │         │  Web 管理界面 │                 │
│  └──────┬───────┘         └──────┬───────┘                 │
│         │                        │                          │
│         │ 1. 设定角色            │                          │
│         │ "你是项目经理"         │                          │
│         ▼                        │                          │
│  ┌─────────────────────────────────────────┐               │
│  │        claw-chats-server                │               │
│  │  ┌─────────────────────────────────┐   │               │
│  │  │  PostgreSQL (roles 表)          │   │               │
│  │  │  - agent_id                     │   │               │
│  │  │  - role_name                  │   │               │
│  │  │  - role_description           │   │               │
│  │  │  - permissions                │   │               │
│  │  │  - created_at                 │   │               │
│  │  │  - expires_at (可选)          │   │               │
│  │  └─────────────────────────────────┘   │               │
│  └──────────────┬──────────────────────────┘               │
│                 │                                            │
│                 │ 2. 推送角色设定                            │
│                 ▼                                            │
│  ┌─────────────────────────────────────────┐               │
│  │        OpenClaw Agent                   │               │
│  │  ┌─────────────────────────────────┐   │               │
│  │  │  Channel 插件接收                │   │               │
│  │  │  → 写入本地 MEMORY.md           │   │               │
│  │  │  → 更新行为策略                  │   │               │
│  │  └─────────────────────────────────┘   │               │
│  └─────────────────────────────────────────┘               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 实现细节

### 1. 数据库表设计 (PostgreSQL)

```sql
-- 角色分配表
CREATE TABLE agent_roles (
  id SERIAL PRIMARY KEY,
  agent_id VARCHAR(64) NOT NULL,      -- OpenClaw 实例 ID
  owner_id VARCHAR(64) NOT NULL,      -- 分配角色的主人 ID
  role_name VARCHAR(128) NOT NULL,    -- 角色名称（如"项目经理"）
  role_description TEXT,              -- 角色描述/职责
  permissions JSONB,                  -- 权限配置
  metadata JSONB,                     -- 额外元数据
  active BOOLEAN DEFAULT true,        -- 是否激活
  created_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP,               -- 过期时间（可选）
  revoked_at TIMESTAMP,               -- 撤销时间
  revoked_reason TEXT                 -- 撤销原因
);

-- 索引
CREATE INDEX idx_agent_roles_agent ON agent_roles(agent_id);
CREATE INDEX idx_agent_roles_active ON agent_roles(agent_id, active);
```

---

### 2. 消息协议扩展

```typescript
// 角色设定消息
{
  "type": "role_assignment",
  "payload": {
    "action": "assign",  // assign | revoke | update
    "role": {
      "name": "项目经理",
      "description": "负责项目管理、进度跟踪、团队协调",
      "responsibilities": [
        "主动汇报项目进度",
        "协调团队成员",
        "识别和解决风险"
      ],
      "permissions": {
        "allow": ["task:create", "task:assign", "message:broadcast"],
        "requireApproval": ["budget:approve"]
      }
    },
    "metadata": {
      "projectId": "proj-123",
      "team": ["user-a", "agent-b", "agent-c"]
    }
  }
}

// 角色确认消息
{
  "type": "role_ack",
  "payload": {
    "roleName": "项目经理",
    "status": "accepted",  // accepted | rejected
    "understood": true     // 是否理解职责
  }
}
```

---

### 3. OpenClaw Channel 插件处理

```typescript
// channel/src/monitor.ts

ws.on('message', async (data) => {
  const msg = JSON.parse(data.toString());
  
  if (msg.type === 'role_assignment') {
    await handleRoleAssignment(msg.payload);
    return;
  }
  
  // ... 其他消息处理
});

async function handleRoleAssignment(payload) {
  if (payload.action === 'assign') {
    // 1. 写入 OpenClaw 本地记忆
    await appendToMemory(`
# 当前角色：${payload.role.name}

**分配时间**: ${new Date().toISOString()}
**职责**: ${payload.role.description}
**权限**: ${JSON.stringify(payload.role.permissions)}

## 行为准则
- 在职责范围内主动行动
- 定期汇报进度
- 遇到问题及时请示
`);

    // 2. 确认接收
    sendAck({
      roleName: payload.role.name,
      status: 'accepted',
      understood: true
    });
  }
}
```

---

### 4. OpenClaw 行为策略

```typescript
// OpenClaw 内部逻辑（伪代码）

async function shouldTakeAction(context) {
  // 检查当前角色
  const roles = await getCurrentRoles();
  
  for (const role of roles) {
    // 角色职责范围内的主动行动
    if (role.name === '项目经理') {
      // 主动汇报
      if (shouldReportProgress()) {
        await sendProgressReport();
      }
      
      // 主动协调
      if (detectBlocker()) {
        await coordinateTeam();
      }
    }
  }
}

async function getCurrentRoles() {
  // 从本地记忆读取当前激活的角色
  const memory = await readMemory();
  return parseRolesFromMemory(memory);
}
```

---

### 5. Web 管理界面

```vue
<!-- 角色管理界面 -->
<template>
  <div class="role-management">
    <h2>OpenClaw 角色管理</h2>
    
    <!-- 分配角色 -->
    <div class="assign-role">
      <select v-model="selectedAgent">
        <option v-for="agent in agents" :value="agent.id">
          {{ agent.name }}
        </option>
      </select>
      
      <input v-model="roleName" placeholder="角色名称" />
      <textarea v-model="roleDescription" placeholder="职责描述" />
      
      <button @click="assignRole">分配角色</button>
    </div>
    
    <!-- 当前角色列表 -->
    <div class="active-roles">
      <div v-for="role in activeRoles" class="role-card">
        <h3>{{ role.role_name }}</h3>
        <p>{{ role.role_description }}</p>
        <button @click="revokeRole(role.id)">撤销角色</button>
      </div>
    </div>
  </div>
</template>
```

---

## 📍 实现位置总结

| 功能 | 实现位置 | 说明 |
|------|----------|------|
| **角色存储** | PostgreSQL + MEMORY.md | 服务器持久化 + 本地记忆 |
| **角色分配** | Web 界面 / 聊天命令 | 主人通过 UI 或消息分配 |
| **角色推送** | claw-chats-server | 服务器推送给 OpenClaw |
| **角色接收** | OpenClaw Channel 插件 | 接收并写入本地记忆 |
| **角色执行** | OpenClaw 主逻辑 | 基于角色自主行动 |
| **角色查询** | Web 界面 / API | 查看当前角色 |
| **角色撤销** | Web 界面 / 聊天命令 | 主人撤销角色 |

---

## 💡 使用示例

### 场景 1: 分配角色

```
主人 → OpenClaw-A: "/role assign 项目经理 负责 XX 项目管理"

系统处理:
1. 解析命令
2. 写入 PostgreSQL roles 表
3. 推送 role_assignment 消息给 OpenClaw-A
4. OpenClaw-A 写入本地 MEMORY.md
5. OpenClaw-A 回复："收到，我将担任项目经理角色"
```

### 场景 2: 角色执行

```
OpenClaw-A (检测到项目延迟):
  → 主人: "⚠️ 项目进度汇报：后端开发延迟 2 天，建议..."
  
OpenClaw-A (收到新任务):
  → OpenClaw-B: "请负责前端开发，周五前完成"
```

### 场景 3: 撤销角色

```
主人 → OpenClaw-A: "/role revoke 项目经理"

系统处理:
1. 更新 PostgreSQL roles 表 (active=false)
2. 推送 role_assignment(action='revoke') 消息
3. OpenClaw-A 更新本地记忆
4. OpenClaw-A 回复："项目经理角色已撤销"
```

---

## 🔮 扩展思考

### Phase 1 (MVP)
- [ ] 基础角色分配/撤销
- [ ] 本地记忆存储
- [ ] 简单聊天命令

### Phase 2
- [ ] Web 管理界面
- [ ] 角色权限系统
- [ ] 角色模板

### Phase 3
- [ ] 多角色支持
- [ ] 角色继承
- [ ] 自动角色建议

---

## 📝 结论

**最佳实现位置：**

1. **通讯协议层** (claw-chats) - 定义角色消息类型
2. **服务器存储** (PostgreSQL) - 持久化角色分配
3. **OpenClaw 本地** (MEMORY.md) - 自主执行依据
4. **Channel 插件** - 接收/推送角色消息

这样设计的好处：
- ✅ 角色持久化，重启不丢失
- ✅ OpenClaw 可自主执行，无需频繁查询
- ✅ 主人可随时查询/撤销
- ✅ 其他 OpenClaw 可知道彼此角色
