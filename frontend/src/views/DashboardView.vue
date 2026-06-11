<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-900 dark:text-gray-100">
      歡迎，{{ authStore.user?.username }}
    </h2>

    <!-- 當月摘要 -->
    <div class="mt-6 grid grid-cols-3 gap-3">
      <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-4">
        <p class="text-xs text-gray-500 dark:text-gray-400">本月支出</p>
        <p class="mt-1 text-lg font-bold text-red-600 dark:text-red-400">
          {{ summary ? `$${summary.expense_total.toLocaleString()}` : '—' }}
        </p>
      </div>
      <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-4">
        <p class="text-xs text-gray-500 dark:text-gray-400">本月收入</p>
        <p class="mt-1 text-lg font-bold text-green-600 dark:text-green-400">
          {{ summary ? `$${summary.income_total.toLocaleString()}` : '—' }}
        </p>
      </div>
      <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-4">
        <p class="text-xs text-gray-500 dark:text-gray-400">損益</p>
        <p class="mt-1 text-lg font-bold" :class="summary && summary.balance >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
          {{ summary ? `${summary.balance >= 0 ? '+' : ''}$${summary.balance.toLocaleString()}` : '—' }}
        </p>
      </div>
    </div>

    <!-- 快速記帳 -->
    <div class="mt-6 bg-white dark:bg-gray-800 shadow rounded-lg p-4">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-sm font-medium text-gray-900 dark:text-gray-100">快速記帳</h3>
          <p class="text-xs text-gray-500 dark:text-gray-400">本月共 {{ summary?.record_count || 0 }} 筆記錄</p>
        </div>
        <router-link to="/accounting"
          class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700">
          新增記帳
        </router-link>
      </div>
    </div>

    <!-- 預算使用狀況 -->
    <div class="mt-6 bg-white dark:bg-gray-800 shadow rounded-lg p-4">
      <h3 class="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">本月預算使用</h3>
      <div v-if="budgetStatus.length > 0" class="space-y-3">
        <div v-for="item in budgetStatus" :key="item.category_id" class="space-y-1">
          <div class="flex items-center justify-between text-sm">
            <span class="text-gray-700 dark:text-gray-300">{{ getCategoryName(item.category_id) }}</span>
            <span :class="item.over ? 'text-red-600 dark:text-red-400 font-medium' : 'text-gray-600 dark:text-gray-400'">
              ${{ item.spent.toLocaleString() }} / ${{ item.budget.toLocaleString() }}
            </span>
          </div>
          <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              class="h-2 rounded-full transition-all"
              :class="item.over ? 'bg-red-500' : item.percentage > 80 ? 'bg-yellow-500' : 'bg-green-500'"
              :style="{ width: Math.min(item.percentage, 100) + '%' }"
            ></div>
          </div>
          <p v-if="item.over" class="text-xs text-red-500 dark:text-red-400">超支 ${{ (item.spent - item.budget).toLocaleString() }}</p>
        </div>
      </div>
      <div v-else class="text-sm text-gray-400 dark:text-gray-500">
        尚未設定預算，<router-link to="/budget" class="text-indigo-600 dark:text-indigo-400 hover:underline">前往設定</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useAccountStore } from '../stores/accounts'
import { budgetApi } from '../api/budget'
import { categoriesApi } from '../api/categories'

const authStore = useAuthStore()
const accountStore = useAccountStore()

const summary = ref(null)
const budgetStatus = ref([])
const categoriesList = ref([
  { id: 1, name: '飲食' },
  { id: 2, name: '生活' },
  { id: 3, name: '居住' },
  { id: 4, name: '交通' },
  { id: 5, name: '娛樂' },
  { id: 6, name: '醫療' },
  { id: 7, name: '其他' },
  { id: 8, name: '投資' },
])

function getCategoryName(typeId) {
  return categoriesList.value.find(c => c.id === typeId)?.name || `類別${typeId}`
}

onMounted(async () => {
  try {
    const result = await categoriesApi.getCategories()
    categoriesList.value = result.categories
  } catch {}

  try {
    summary.value = await accountStore.fetchSummary()
  } catch {}

  try {
    const result = await budgetApi.getBudgetStatus()
    budgetStatus.value = result.status.filter(s => s.budget > 0)
  } catch {}
})
</script>
