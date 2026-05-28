<template>
  <div>
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-bold text-gray-900">月帳統計</h2>
      <MonthPicker v-model="currentMonth" @update:model-value="loadSummary" />
    </div>

    <!-- Loading -->
    <div v-if="loading" class="mt-8 text-center text-gray-500">載入中...</div>

    <!-- 錯誤 -->
    <div v-if="error" class="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
      {{ error }}
    </div>

    <!-- 統計內容 -->
    <div v-if="summary && !loading" class="mt-6 space-y-6">
      <!-- 摘要卡片 -->
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div class="bg-white shadow rounded-lg p-5">
          <p class="text-sm font-medium text-gray-500">支出總計</p>
          <p class="mt-1 text-2xl font-bold text-red-600">${{ summary.expense_total.toLocaleString() }}</p>
        </div>
        <div class="bg-white shadow rounded-lg p-5">
          <p class="text-sm font-medium text-gray-500">收入總計</p>
          <p class="mt-1 text-2xl font-bold text-green-600">${{ summary.income_total.toLocaleString() }}</p>
        </div>
        <div class="bg-white shadow rounded-lg p-5">
          <p class="text-sm font-medium text-gray-500">收支損益</p>
          <p class="mt-1 text-2xl font-bold" :class="summary.balance >= 0 ? 'text-green-600' : 'text-red-600'">
            {{ summary.balance >= 0 ? '+' : '' }}${{ summary.balance.toLocaleString() }}
          </p>
        </div>
      </div>

      <!-- 圓餅圖 + 類別明細 -->
      <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <!-- 圓餅圖 -->
        <div class="bg-white shadow rounded-lg p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">支出分佈</h3>
          <div v-if="chartData.length > 0" class="max-w-xs mx-auto">
            <PieChart :labels="chartLabels" :data="chartData" />
          </div>
          <p v-else class="text-center text-gray-500 py-8">本月無支出記錄</p>
        </div>

        <!-- 類別明細 -->
        <div class="bg-white shadow rounded-lg p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">各類別明細</h3>
          <div class="space-y-3">
            <div
              v-for="cat in summary.categories"
              :key="cat.type"
              class="flex items-center justify-between"
            >
              <div class="flex items-center space-x-3">
                <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                  {{ getCategoryName(cat.type) }}
                </span>
              </div>
              <div class="text-right">
                <span class="text-sm font-medium text-gray-900">${{ cat.total.toLocaleString() }}</span>
                <span class="ml-2 text-xs text-gray-500">({{ cat.percentage }}%)</span>
              </div>
            </div>
            <div v-if="summary.categories.length === 0" class="text-center text-gray-500 py-4">
              本月無支出記錄
            </div>
          </div>

          <!-- 記錄筆數 -->
          <div class="mt-4 pt-4 border-t border-gray-200">
            <p class="text-sm text-gray-500">本月共 {{ summary.record_count }} 筆記錄</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 無資料 -->
    <div v-if="!summary && !loading && !error" class="mt-8 text-center text-gray-500">
      本月沒有記帳記錄
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAccountStore } from '../stores/accounts'
import PieChart from '../components/PieChart.vue'
import MonthPicker from '../components/MonthPicker.vue'

const accountStore = useAccountStore()

const currentMonth = ref(accountStore.currentMonth)
const summary = ref(null)
const loading = ref(false)
const error = ref(null)

const categories = [
  { id: 1, name: '飲食' },
  { id: 2, name: '生活' },
  { id: 3, name: '居住' },
  { id: 4, name: '交通' },
  { id: 5, name: '娛樂' },
  { id: 6, name: '醫療' },
  { id: 7, name: '其他' },
  { id: 8, name: '投資' },
]

function getCategoryName(typeId) {
  return categories.find(c => c.id === typeId)?.name || `類別${typeId}`
}

const chartLabels = computed(() => {
  if (!summary.value) return []
  return summary.value.categories.map(c => getCategoryName(c.type))
})

const chartData = computed(() => {
  if (!summary.value) return []
  return summary.value.categories.map(c => c.total)
})

async function loadSummary(month) {
  loading.value = true
  error.value = null
  try {
    const targetMonth = month || currentMonth.value
    summary.value = await accountStore.fetchSummary(targetMonth)
  } catch (err) {
    error.value = err.message || '載入統計失敗'
    summary.value = null
  } finally {
    loading.value = false
  }
}

onMounted(() => loadSummary())
</script>
