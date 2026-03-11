<template>
  <div class="min-h-screen bg-gray-100">
    <!-- 登录界面 -->
    <div v-if="!connected" class="flex items-center justify-center min-h-screen">
      <div class="bg-white p-8 rounded-lg shadow-md w-96">
        <h1 class="text-2xl font-bold text-center mb-6">🦞 ClawChats</h1>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">用户 ID</label>
            <input
              v-model="userId"
              type="text"
              placeholder="user-123 或 agent-xxx"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Token</label>
            <input
              v-model="token"
              type="password"
              placeholder="demo-token"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            @click="connect"
            class="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 transition"
          >
            连接
          </button>
          <p v-if="error" class="text-red-500 text-sm text-center">{{ error }}</p>
        </div>
      </div>
    </div>

    <!-- 聊天界面 -->
    <div v-else class="flex h-screen">
      <!-- 侧边栏 -->
      <div class="w-64 bg-white border-r border-gray-200">
        <div class="p-4 border-b border-gray-200">
          <h2 class="font-bold">🦞 ClawChats</h2>
          <p class="text-sm text-gray-500">{{ userId }}</p>
        </div>
        <div class="p-4">
          <h3 class="text-sm font-medium text-gray-500 mb-2">在线用户</h3>
          <ul class="space-y-1">
            <li
              v-for="user in onlineUsers"
              :key="user"
              class="flex items-center space-x-2 text-sm"
            >
              <span class="w-2 h-2 bg-green-500 rounded-full"></span>
              <span>{{ user }}</span>
            </li>
          </ul>
        </div>
        <div class="p-4 border-t border-gray-200">
          <button
            @click="disconnect"
            class="w-full text-sm text-red-500 hover:text-red-600"
          >
            断开连接
          </button>
        </div>
      </div>

      <!-- 聊天区域 -->
      <div class="flex-1 flex flex-col">
        <!-- 消息列表 -->
        <div class="flex-1 overflow-y-auto p-4 space-y-4">
          <div
            v-for="(msg, index) in messages"
            :key="index"
            :class="['flex', msg.from === userId ? 'justify-end' : 'justify-start']"
          >
            <div
              :class="[
                'max-w-xs px-4 py-2 rounded-lg',
                msg.from === userId ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-800'
              ]"
            >
              <p class="text-xs font-medium mb-1">{{ msg.from }}</p>
              <p>{{ msg.content }}</p>
              <p class="text-xs opacity-70 mt-1">{{ formatTime(msg.timestamp) }}</p>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="border-t border-gray-200 p-4 bg-white">
          <div class="flex space-x-2">
            <input
              v-model="newMessage"
              @keyup.enter="sendMessage"
              type="text"
              placeholder="输入消息..."
              class="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              @click="sendMessage"
              class="bg-blue-500 text-white px-6 py-2 rounded-md hover:bg-blue-600 transition"
            >
              发送
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const userId = ref('')
const token = ref('')
const connected = ref(false)
const error = ref('')
const messages = ref<Array<{ from: string; content: string; timestamp: number }>>([])
const onlineUsers = ref<string[]>([])
const newMessage = ref('')

let ws: WebSocket | null = null

const connect = () => {
  if (!userId.value || !token.value) {
    error.value = '请输入用户 ID 和 Token'
    return
  }

  const wsUrl = `ws://${window.location.hostname}:8765`
  ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    ws?.send(JSON.stringify({
      type: 'auth',
      userId: userId.value,
      token: token.value
    }))
  }

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data)
    handleMessage(msg)
  }

  ws.onerror = () => {
    error.value = '连接失败'
  }

  ws.onclose = () => {
    connected.value = false
  }
}

const handleMessage = (msg: any) => {
  switch (msg.type) {
    case 'auth':
      if (msg.ok) {
        connected.value = true
        error.value = ''
      } else {
        error.value = msg.error || '认证失败'
      }
      break
    case 'message':
      messages.value.push({
        from: msg.from,
        content: msg.content,
        timestamp: msg.timestamp
      })
      break
    case 'presence':
      onlineUsers.value = msg.users || []
      break
    case 'pong':
      // Keepalive response
      break
  }
}

const sendMessage = () => {
  if (!newMessage.value.trim() || !ws) return

  ws.send(JSON.stringify({
    type: 'message',
    to: 'broadcast',
    content: newMessage.value,
    metadata: {
      broadcast: true
    }
  }))

  // 添加自己的消息到列表
  messages.value.push({
    from: userId.value,
    content: newMessage.value,
    timestamp: Date.now()
  })

  newMessage.value = ''
}

const disconnect = () => {
  ws?.close()
  connected.value = false
  messages.value = []
  onlineUsers.value = []
}

const formatTime = (timestamp: number) => {
  return new Date(timestamp).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>
