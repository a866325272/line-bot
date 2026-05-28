<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <!-- Header -->
      <div class="text-center">
        <h1 class="text-3xl font-bold text-gray-900">記帳 Web UI</h1>
        <p class="mt-2 text-sm text-gray-600">管理你的收支記錄</p>
      </div>

      <!-- Tab 切換 -->
      <div class="flex border-b border-gray-200">
        <button
          @click="activeTab = 'login'"
          :class="[
            'flex-1 py-3 text-center font-medium text-sm border-b-2 transition-colors',
            activeTab === 'login'
              ? 'border-indigo-500 text-indigo-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          ]"
        >
          登入
        </button>
        <button
          @click="activeTab = 'register'"
          :class="[
            'flex-1 py-3 text-center font-medium text-sm border-b-2 transition-colors',
            activeTab === 'register'
              ? 'border-indigo-500 text-indigo-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          ]"
        >
          註冊
        </button>
      </div>

      <!-- 錯誤訊息 -->
      <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
        {{ error }}
      </div>

      <!-- 登入表單 -->
      <form v-if="activeTab === 'login'" @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label for="login-username" class="block text-sm font-medium text-gray-700">使用者名稱</label>
          <input
            id="login-username"
            v-model="loginForm.username"
            type="text"
            required
            autocomplete="username"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            placeholder="輸入使用者名稱"
          />
        </div>
        <div>
          <label for="login-password" class="block text-sm font-medium text-gray-700">密碼</label>
          <input
            id="login-password"
            v-model="loginForm.password"
            type="password"
            required
            autocomplete="current-password"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            placeholder="輸入密碼"
          />
        </div>
        <button
          type="submit"
          :disabled="loading"
          class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ loading ? '登入中...' : '登入' }}
        </button>
      </form>

      <!-- 註冊表單 -->
      <form v-if="activeTab === 'register'" @submit.prevent="handleRegister" class="space-y-4">
        <div>
          <label for="reg-username" class="block text-sm font-medium text-gray-700">使用者名稱</label>
          <input
            id="reg-username"
            v-model="registerForm.username"
            type="text"
            required
            autocomplete="username"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            placeholder="至少 3 個字元"
          />
        </div>
        <div>
          <label for="reg-password" class="block text-sm font-medium text-gray-700">密碼</label>
          <input
            id="reg-password"
            v-model="registerForm.password"
            type="password"
            required
            autocomplete="new-password"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            placeholder="至少 8 字元，含大小寫和數字"
          />
        </div>
        <div>
          <label for="reg-confirm" class="block text-sm font-medium text-gray-700">確認密碼</label>
          <input
            id="reg-confirm"
            v-model="registerForm.confirmPassword"
            type="password"
            required
            autocomplete="new-password"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            placeholder="再次輸入密碼"
          />
        </div>

        <!-- 進階選項：綁定現有 Firestore Document -->
        <div>
          <button
            type="button"
            @click="showAdvanced = !showAdvanced"
            class="text-sm text-indigo-600 hover:text-indigo-500"
          >
            {{ showAdvanced ? '▼ 隱藏進階選項' : '▶ 進階選項（綁定現有資料）' }}
          </button>
          <div v-if="showAdvanced" class="mt-2">
            <label for="reg-docid" class="block text-sm font-medium text-gray-700">
              Firestore Document ID（選填）
            </label>
            <input
              id="reg-docid"
              v-model="registerForm.firestoreDocId"
              type="text"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="留空則自動建立新的"
            />
            <p class="mt-1 text-xs text-gray-500">如果你已有 LINE Bot 記帳資料，填入對應的 Document ID 即可綁定</p>
          </div>
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ loading ? '註冊中...' : '註冊' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const activeTab = ref('login')
const showAdvanced = ref(false)
const error = ref(null)

const loading = computed(() => authStore.loading)

const loginForm = ref({
  username: '',
  password: '',
})

const registerForm = ref({
  username: '',
  password: '',
  confirmPassword: '',
  firestoreDocId: '',
})

async function handleLogin() {
  error.value = null
  try {
    await authStore.login(loginForm.value.username, loginForm.value.password)
    router.push('/')
  } catch (err) {
    error.value = err.message || '登入失敗'
  }
}

async function handleRegister() {
  error.value = null

  // 前端驗證
  if (registerForm.value.password !== registerForm.value.confirmPassword) {
    error.value = '兩次密碼不一致'
    return
  }

  try {
    await authStore.register(
      registerForm.value.username,
      registerForm.value.password,
      registerForm.value.firestoreDocId || null
    )
    router.push('/')
  } catch (err) {
    error.value = err.message || '註冊失敗'
  }
}
</script>
