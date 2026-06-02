<template>
  <div class="min-h-screen flex flex-col lg:flex-row">
    <!-- Desktop Sidebar (hidden on mobile) -->
    <aside class="hidden lg:flex lg:flex-col lg:w-64 lg:fixed lg:inset-y-0 bg-white border-r border-gray-200">
      <div class="flex items-center h-16 px-4 border-b border-gray-200">
        <h1 class="text-lg font-bold text-gray-900">記帳 Web UI</h1>
      </div>

      <nav class="mt-4 px-2 space-y-1 flex-1">
        <router-link
          v-for="item in allNavItems"
          :key="item.path"
          :to="item.path"
          class="flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors"
          :class="[
            isActive(item.path)
              ? 'bg-indigo-50 text-indigo-700'
              : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
          ]"
        >
          <span class="mr-3 text-lg">{{ item.icon }}</span>
          {{ item.name }}
        </router-link>
      </nav>

      <div class="p-4 border-t border-gray-200">
        <div class="flex items-center justify-between">
          <span class="text-sm text-gray-700">{{ authStore.user?.username }}</span>
          <button @click="handleLogout" class="text-sm text-gray-500 hover:text-gray-700">登出</button>
        </div>
      </div>
    </aside>

    <!-- Main content -->
    <div class="flex-1 flex flex-col lg:ml-64">
      <!-- Mobile top bar -->
      <header class="lg:hidden sticky top-0 z-10 flex items-center justify-between h-12 px-4 bg-white border-b border-gray-200">
        <h1 class="text-sm font-bold text-gray-900">記帳 Web UI</h1>
        <div class="flex items-center space-x-3">
          <span class="text-xs text-gray-500">{{ authStore.user?.username }}</span>
          <button @click="handleLogout" class="text-xs text-gray-500 hover:text-gray-700">登出</button>
        </div>
      </header>

      <!-- Page content (add bottom padding on mobile for tab bar) -->
      <main class="flex-1 p-4 sm:p-6 lg:p-8 overflow-auto pb-20 lg:pb-8">
        <router-view />
      </main>
    </div>

    <!-- Mobile Bottom Tab Bar (hidden on desktop) -->
    <nav class="lg:hidden fixed bottom-0 inset-x-0 z-30 bg-white border-t border-gray-200 safe-area-bottom">
      <div class="flex items-center justify-around h-16">
        <router-link
          v-for="item in bottomNavItems"
          :key="item.path"
          :to="item.path"
          class="flex flex-col items-center justify-center flex-1 h-full transition-colors"
          :class="[
            isActive(item.path)
              ? 'text-indigo-600'
              : 'text-gray-500 hover:text-gray-700'
          ]"
        >
          <!-- 記帳按鈕突出 -->
          <template v-if="item.highlight">
            <div class="flex items-center justify-center w-12 h-12 -mt-4 bg-indigo-600 rounded-full shadow-lg">
              <span class="text-xl text-white">{{ item.icon }}</span>
            </div>
            <span class="text-xs mt-0.5">{{ item.name }}</span>
          </template>
          <template v-else>
            <span class="text-xl">{{ item.icon }}</span>
            <span class="text-xs mt-1">{{ item.name }}</span>
          </template>
        </router-link>

        <!-- 更多按鈕 -->
        <button
          @click="moreMenuOpen = !moreMenuOpen"
          class="flex flex-col items-center justify-center flex-1 h-full transition-colors"
          :class="moreMenuOpen ? 'text-indigo-600' : 'text-gray-500'"
        >
          <span class="text-xl">⋯</span>
          <span class="text-xs mt-1">更多</span>
        </button>
      </div>

      <!-- 更多選單 -->
      <div
        v-if="moreMenuOpen"
        class="absolute bottom-16 right-2 w-48 bg-white rounded-lg shadow-xl border border-gray-200 py-2"
      >
        <router-link
          v-for="item in moreNavItems"
          :key="item.path"
          :to="item.path"
          class="flex items-center px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50"
          @click="moreMenuOpen = false"
        >
          <span class="mr-3">{{ item.icon }}</span>
          {{ item.name }}
        </router-link>
      </div>
    </nav>

    <!-- More menu overlay (mobile) -->
    <div
      v-if="moreMenuOpen"
      class="lg:hidden fixed inset-0 z-20"
      @click="moreMenuOpen = false"
    ></div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const moreMenuOpen = ref(false)

// 所有導航項目（桌面側邊欄用）
const allNavItems = [
  { path: '/', name: '儀表板', icon: '📊' },
  { path: '/accounting', name: '記帳', icon: '✏️' },
  { path: '/statistics', name: '統計與趨勢', icon: '📈' },
  { path: '/detail', name: '明細', icon: '📋' },
  { path: '/budget', name: '預算設定', icon: '💰' },
  { path: '/categories', name: '類別管理', icon: '🏷️' },
  { path: '/settings', name: '個人設定', icon: '⚙️' },
]

// 底部 tab bar 項目（手機用，最多 4 個 + 更多）
const bottomNavItems = [
  { path: '/', name: '首頁', icon: '📊' },
  { path: '/detail', name: '明細', icon: '📋' },
  { path: '/accounting', name: '記帳', icon: '✏️', highlight: true },
  { path: '/statistics', name: '統計', icon: '📈' },
]

// 「更多」選單項目
const moreNavItems = [
  { path: '/budget', name: '預算設定', icon: '💰' },
  { path: '/categories', name: '類別管理', icon: '🏷️' },
  { path: '/settings', name: '個人設定', icon: '⚙️' },
]

function isActive(path) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.safe-area-bottom {
  padding-bottom: env(safe-area-inset-bottom, 0px);
}
</style>
