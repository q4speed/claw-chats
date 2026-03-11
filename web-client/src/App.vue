<template>
  <div class="min-h-screen bg-gray-100">
    <!-- 未登录：显示登录/注册界面 -->
    <div v-if="!currentUser" class="flex items-center justify-center min-h-screen">
      <div class="bg-white p-8 rounded-lg shadow-md w-96">
        <h1 class="text-2xl font-bold text-center mb-6">🦞 ClawChats</h1>
        
        <!-- 切换标签 -->
        <div class="flex mb-4 border-b">
          <button
            @click="showLogin = true"
            :class="['flex-1 py-2', showLogin ? 'border-b-2 border-blue-500 text-blue-500' : 'text-gray-500']"
          >
            登录
          </button>
          <button
            @click="showLogin = false"
            :class="['flex-1 py-2', !showLogin ? 'border-b-2 border-blue-500 text-blue-500' : 'text-gray-500']"
          >
            注册
          </button>
        </div>
        
        <!-- 登录表单 -->
        <div v-if="showLogin" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">用户名</label>
            <input
              v-model="loginForm.username"
              type="text"
              placeholder="请输入用户名"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">密码</label>
            <input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            @click="handleLogin"
            class="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 transition"
          >
            登录
          </button>
          <p v-if="error" class="text-red-500 text-sm text-center">{{ error }}</p>
        </div>
        
        <!-- 注册表单 -->
        <div v-else class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">用户名</label>
            <input
              v-model="registerForm.username"
              type="text"
              placeholder="3-64 个字符"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">密码</label>
            <input
              v-model="registerForm.password"
              type="password"
              placeholder="至少 6 个字符"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">邮箱（可选）</label>
            <input
              v-model="registerForm.email"
              type="email"
              placeholder="example@email.com"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            @click="handleRegister"
            class="w-full bg-green-500 text-white py-2 px-4 rounded-md hover:bg-green-600 transition"
          >
            注册
          </button>
          <p v-if="error" class="text-red-500 text-sm text-center">{{ error }}</p>
          <p v-if="success" class="text-green-500 text-sm text-center">{{ success }}</p>
        </div>
      </div>
    </div>

    <!-- 已登录：显示主界面 -->
    <div v-else class="flex h-screen">
      <!-- 侧边栏 -->
      <div class="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div class="p-4 border-b border-gray-200">
          <h2 class="font-bold">🦞 ClawChats</h2>
          <p class="text-sm text-gray-500">{{ currentUser.username }}</p>
        </div>
        
        <!-- 群组列表 -->
        <div class="flex-1 overflow-y-auto p-4">
          <div class="flex justify-between items-center mb-2">
            <h3 class="text-sm font-medium text-gray-500">我的群组</h3>
            <button @click="showCreateGroup = true" class="text-blue-500 hover:text-blue-600">+</button>
          </div>
          <ul class="space-y-1">
            <li
              v-for="group in groups"
              :key="group.id"
              @click="selectGroup(group)"
              :class="['cursor-pointer p-2 rounded hover:bg-gray-100', selectedGroup?.id === group.id ? 'bg-blue-50' : '']"
            >
              {{ group.name }}
            </li>
          </ul>
        </div>
        
        <div class="p-4 border-t border-gray-200">
          <button @click="logout" class="w-full text-sm text-red-500 hover:text-red-600">
            退出登录
          </button>
        </div>
      </div>

      <!-- 聊天区域 -->
      <div class="flex-1 flex flex-col">
        <!-- 群聊界面 -->
        <div v-if="selectedGroup" class="flex-1 flex flex-col">
          <div class="p-4 border-b border-gray-200">
            <h2 class="font-bold">{{ selectedGroup.name }}</h2>
            <p class="text-sm text-gray-500">{{ selectedGroup.description || '暂无描述' }}</p>
          </div>
          
          <!-- 消息列表 -->
          <div class="flex-1 overflow-y-auto p-4 space-y-4">
            <div v-for="msg in groupMessages" :key="msg.id" class="flex">
              <div class="bg-gray-200 px-4 py-2 rounded-lg">
                <p class="text-xs font-medium text-gray-600">{{ msg.username }}</p>
                <p>{{ msg.content }}</p>
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
              <button @click="sendMessage" class="bg-blue-500 text-white px-6 py-2 rounded-md hover:bg-blue-600">
                发送
              </button>
            </div>
          </div>
        </div>
        
        <!-- 未选择群组 -->
        <div v-else class="flex-1 flex items-center justify-center text-gray-500">
          <p>选择一个群组开始聊天</p>
        </div>
      </div>
    </div>

    <!-- 创建群组弹窗 -->
    <div v-if="showCreateGroup" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div class="bg-white p-6 rounded-lg w-96">
        <h3 class="text-lg font-bold mb-4">创建群组</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">群名称</label>
            <input
              v-model="newGroup.name"
              type="text"
              placeholder="请输入群名称"
              class="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">群描述（可选）</label>
            <textarea
              v-model="newGroup.description"
              placeholder="请输入群描述"
              class="w-full px-3 py-2 border border-gray-300 rounded-md"
            ></textarea>
          </div>
          <div class="flex space-x-2">
            <button @click="createGroup" class="flex-1 bg-blue-500 text-white py-2 rounded-md hover:bg-blue-600">
              创建
            </button>
            <button @click="showCreateGroup = false" class="flex-1 bg-gray-300 text-gray-700 py-2 rounded-md hover:bg-gray-400">
              取消
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'

const API_URL = 'http://localhost:8766/api/v1'

// 认证状态
const currentUser = ref<any>(null)
const token = ref('')
const showLogin = ref(true)

// 表单
const loginForm = reactive({ username: '', password: '' })
const registerForm = reactive({ username: '', password: '', email: '' })
const newGroup = reactive({ name: '', description: '' })

// 状态
const error = ref('')
const success = ref('')
const groups = ref<any[]>([])
const selectedGroup = ref<any>(null)
const groupMessages = ref<any[]>([])
const newMessage = ref('')
const showCreateGroup = ref(false)

// 登录
const handleLogin = async () => {
  error.value = ''
  try {
    const res = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(loginForm)
    })
    const data = await res.json()
    
    if (!res.ok) throw new Error(data.detail)
    
    token.value = data.access_token
    currentUser.value = { id: data.user_id, username: data.username }
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user', JSON.stringify({ id: data.user_id, username: data.username }))
    
    loadGroups()
  } catch (e: any) {
    error.value = e.message
  }
}

// 注册
const handleRegister = async () => {
  error.value = ''
  success.value = ''
  try {
    const res = await fetch(`${API_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(registerForm)
    })
    const data = await res.json()
    
    if (!res.ok) throw new Error(data.detail)
    
    success.value = '注册成功！请登录'
    showLogin.value = true
  } catch (e: any) {
    error.value = e.message
  }
}

// 登出
const logout = () => {
  currentUser.value = null
  token.value = ''
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}

// 加载群组
const loadGroups = async () => {
  if (!currentUser.value) return
  try {
    const res = await fetch(`${API_URL}/users/${currentUser.value.id}/groups`)
    const data = await res.json()
    groups.value = data
  } catch (e) {
    console.error('加载群组失败', e)
  }
}

// 选择群组
const selectGroup = (group: any) => {
  selectedGroup.value = group
  // TODO: 加载群消息
}

// 创建群组
const createGroup = async () => {
  if (!newGroup.name) return
  try {
    const res = await fetch(`${API_URL}/groups?owner_id=${currentUser.value.id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newGroup)
    })
    const data = await res.json()
    
    if (!res.ok) throw new Error(data.detail)
    
    showCreateGroup.value = false
    newGroup.name = ''
    newGroup.description = ''
    loadGroups()
  } catch (e: any) {
    error.value = e.message
  }
}

// 发送消息
const sendMessage = () => {
  if (!newMessage.value.trim()) return
  // TODO: 发送到 WebSocket
  newMessage.value = ''
}

// 初始化
onMounted(() => {
  const savedUser = localStorage.getItem('user')
  const savedToken = localStorage.getItem('token')
  if (savedUser && savedToken) {
    currentUser.value = JSON.parse(savedUser)
    token.value = savedToken
    loadGroups()
  }
})
</script>
