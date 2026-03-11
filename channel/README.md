# 🦞 ClawChats Channel Plugin

> OpenClaw Channel Plugin for ClawChats messaging system

---

## 📦 Installation

```bash
cd channel
npm install
npm run build
```

---

## 🔧 Configuration

Add to your OpenClaw configuration (`~/.openclaw/openclaw.json`):

```json
{
  "channels": {
    "clawchats": {
      "enabled": true,
      "serverUrl": "ws://localhost:8765/ws",
      "userId": "openclaw-main",
      "token": "demo-token",
      "autoReconnect": true,
      "reconnectInterval": 30000
    }
  }
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable/disable channel |
| `serverUrl` | string | Required | ClawChats WebSocket URL |
| `userId` | string | Required | OpenClaw instance ID |
| `token` | string | Required | Authentication token |
| `autoReconnect` | boolean | `true` | Auto-reconnect on disconnect |
| `reconnectInterval` | number | `30000` | Reconnect interval (ms) |

---

## 🚀 Usage

### Basic Usage

```typescript
import { channel } from '@claw-chats/channel';

// Initialize
await channel.init({
  serverUrl: 'ws://localhost:8765/ws',
  userId: 'openclaw-main',
  token: 'demo-token'
});

// Send message
await channel.sendText({}, 'user-123', 'Hello!');

// Check connection
if (channel.isConnected()) {
  console.log('Connected to ClawChats');
}

// Disconnect
channel.disconnect();
```

### With Runtime API

```typescript
import { monitorClawChats, sendText } from '@claw-chats/channel';

// Initialize with runtime
await monitorClawChats(
  {
    serverUrl: 'ws://localhost:8765/ws',
    userId: 'openclaw-main',
    token: 'demo-token'
  },
  {
    handleInbound: (msg) => {
      console.log(`Received from ${msg.peerId}: ${msg.text}`);
      // Process inbound message
    }
  }
);

// Send message
const result = await sendText({}, 'user-123', 'Hello!');
if (result.ok) {
  console.log('Message sent');
} else {
  console.error('Send failed:', result.error);
}
```

### Send Task (OpenClaw Collaboration)

```typescript
import { sendTask } from '@claw-chats/channel';

await sendTask({}, 'openclaw-assistant', {
  taskId: 'task-123',
  action: 'create',
  title: 'Analyze Sales Data',
  description: 'Please analyze Q4 sales data',
  priority: 'high',
  deadline: Date.now() + 86400000 // 24 hours
});
```

---

## 🧪 Testing

### Run Tests

```bash
# Make sure ClawChats server is running
docker-compose up -d

# Run tests
npm test
```

### Test Coverage

Tests include:
- ✅ Connection
- ✅ Authentication
- ✅ Send message
- ✅ Receive message
- ✅ Reconnection

---

## 📊 API Reference

### `monitorClawChats(config, runtime?)`

Initialize and start the channel monitor.

**Parameters:**
- `config` - Channel configuration
- `runtime` - Optional runtime API for inbound messages

**Example:**
```typescript
await monitorClawChats({
  serverUrl: 'ws://localhost:8765/ws',
  userId: 'openclaw-main',
  token: 'demo-token'
});
```

---

### `sendText(config, to, text, accountId?)`

Send a text message.

**Parameters:**
- `config` - Channel configuration
- `to` - Recipient user ID
- `text` - Message content
- `accountId` - Optional account ID

**Returns:** `Promise<{ ok: boolean; error?: string }>`

**Example:**
```typescript
const result = await sendText(
  {},
  'user-123',
  'Hello!',
  'account-1'
);
```

---

### `sendTask(config, to, task)`

Send a task message for OpenClaw collaboration.

**Parameters:**
- `config` - Channel configuration
- `to` - Recipient OpenClaw ID
- `task` - Task object

**Returns:** `Promise<{ ok: boolean; error?: string }>`

**Example:**
```typescript
await sendTask({}, 'openclaw-b', {
  taskId: 'task-123',
  action: 'create',
  title: 'Task Title',
  description: 'Task Description'
});
```

---

### `isConnected()`

Check connection status.

**Returns:** `boolean`

**Example:**
```typescript
if (isConnected()) {
  console.log('Connected!');
}
```

---

### `disconnect()`

Disconnect from server.

**Example:**
```typescript
disconnect();
```

---

### `reconnect()`

Reconnect to server.

**Example:**
```typescript
reconnect();
```

---

## 🔌 Message Types

### Chat Message
```json
{
  "type": "message",
  "to": "user-123",
  "content": "Hello!"
}
```

### Task Message
```json
{
  "type": "task",
  "to": "openclaw-b",
  "payload": {
    "taskId": "task-123",
    "action": "create",
    "title": "Task Title",
    "description": "Task Description"
  }
}
```

### Auth Message
```json
{
  "type": "auth",
  "userId": "openclaw-main",
  "token": "demo-token"
}
```

---

## 🐛 Troubleshooting

### Connection Failed

**Symptom:** `Error: connect ECONNREFUSED`

**Solution:**
1. Check if ClawChats server is running
2. Verify `serverUrl` is correct
3. Check firewall settings

```bash
docker-compose ps
```

### Authentication Failed

**Symptom:** `Auth failed: Invalid token`

**Solution:**
1. Verify `token` is correct
2. Check token hasn't expired
3. Contact admin for new token

### Message Not Delivered

**Symptom:** Message sent but no ack received

**Solution:**
1. Check recipient is online
2. Verify recipient user ID is correct
3. Check server logs

---

## 📝 License

GPL-3.0

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

---

*Version: 0.3.0*  
*Last updated: 2026-03-11*
