<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-900">
      歡迎，{{ authStore.user?.username }}
    </h2>
    <p class="mt-2 text-gray-600">記帳 Web UI — 管理你的收支記錄</p>

    <!-- 當月摘要 -->
    <div class="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
      <div class="bg-white overflow-hidden shadow rounded-lg p-6">
        <h3 class="text-sm font-medium text-gray-500">本月支出</h3>
        <p class="mt-2 text-3xl font-bold text-red-600">
          {{ summary ? `$${summary.expense_total.toLocaleString()}` : '—' }}
        </p>
      </div>

      <div class="bg-white overflow-hidden shadow rounded-lg p-6">
        <h3 class="text-sm font-medium text-gray-500">本月收入</h3>
        <p class="mt-2 text-3xl font-bold text-green-600">
          {{ summary ? `$${summary.income_total.toLocaleString()}` : '—' }}
        </p>
      </div>

      <div class="bg-white overflow-hidden shadow rounded-lg p-6">
        <h3 class="text-sm font-medium text-gray-500">收支損益</h3>
        <p class="mt-2 text-3xl font-bold" :class="summary && summary.balance >= 0 ? 'text-green-600' : 'text-red-600'">
          {{ summary ? `${summary.balance >= 0 ? '+' : ''}$${summary.balance.toLocaleString()}` : '—' }}
        </p>
      </div>
    </div>

    <!-- 快速記帳提示 -->
    <div class="mt-8 bg-white shadow rounded-lg p-6">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-lg font-medium text-gray-900">快速記帳</h3>
          <p class="mt-1 text-sm text-gray-500">本月共 {{ summary?.record_count || 0 }} 筆記錄</p>
        </div>
        <router-link
          to="/accounting"
          class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700"
        >
          新增記帳
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useAccountStore } from '../stores/accounts'

const authStore = useAuthStore()
const accountStore = useAccountStore()

const summary = ref(null)

onMounted(async () => {
  try {
    summary.value = await accountStore.fetchSummary()
  } catch {
    // 靜默失敗（可能還沒有資料）
  }
})
</script>
