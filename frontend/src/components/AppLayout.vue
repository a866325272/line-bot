<template>
  <div class="min-h-screen flex">
    <!-- Sidebar -->
    <aside
      :class="[
        'fixed inset-y-0 left-0 z-30 w-64 bg-white border-r border-gray-200 transform transition-transform duration-200 ease-in-out lg:translate-x-0 lg:static lg:inset-auto',
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      ]"
    >
      <div class="flex items-center justify-between h-16 px-4 border-b border-gray-200">
        <h1 class="text-lg font-bold text-gray-900">記帳 Web UI</h1>
        <button @click="sidebarOpen = false" class="lg:hidden text-gray-500 hover:text-gray-700">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <nav class="mt-4 px-2 space-y-1">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors"
          :class="[
            $route.path === item.path
              ? 'bg-indigo-50 text-indigo-700'
              : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
          ]"
          @click="sidebarOpen = false"
        >
          <span class="mr-3">{{ item.icon }}</span>
          {{ item.name }}
        </router-link>
      </nav>
    </aside>

    <!-- Sidebar overlay (mobile) -->
    <div
      v-if="sidebarOpen"
      class="fixed inset-0 z-20 bg-black bg-opacity-50 lg:hidden"
      @click="sidebarOpen = false"
    ></div>

    <!-- Main content -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Top navbar -->
      <header class="sticky top-0 z-10 flex items-center justify-between h-16 px-4 bg-white border-b border-gray-200">
        <button @click="sidebarOpen = true" class="lg:hidden text-gray-500 hover:text-gray-700">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <div class="flex items-center space-x-4 ml-auto">
          <span class="text-sm text-gray-700">{{ authStore.user?.username }}</span>
          <button
            @click="handleLogout"
            class="text-sm text-gray-500 hover:text-gray-700 px-3 py-1 rounded-md hover:bg-gray-100"
          >
            登出
          </button>
        </div>
      </header>

      <!-- Page content -->
      <main class="flex-1 p-4 sm:p-6 lg:p-8 overflow-auto">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const sidebarOpen = ref(false)

const navItems = [
  { path: '/', name: '儀表板', icon: '📊' },
  { path: '/accounting', name: '記帳', icon: '✏️' },
  { path: '/monthly', name: '月帳統計', icon: '📈' },
  { path: '/detail', name: '明細', icon: '📋' },
  { path: '/categories', name: '類別管理', icon: '🏷️' },
  { path: '/budget', name: '預算設定', icon: '💰' },
  { path: '/settings', name: '個人設定', icon: '⚙️' },
]

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>
