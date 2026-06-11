<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-900 dark:text-gray-100">統計與趨勢</h2>

    <!-- 日期區間選擇 -->
    <div class="mt-4 bg-white dark:bg-gray-800 shadow rounded-lg p-4">
      <div class="flex flex-wrap items-end gap-3">
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400">起始日期</label>
          <input v-model="startDate" type="date"
            class="mt-1 px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100" />
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400">結束日期</label>
          <input v-model="endDate" type="date"
            class="mt-1 px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100" />
        </div>
        <button @click="loadData" :disabled="loading"
          class="px-4 py-1.5 bg-indigo-600 text-white text-sm rounded-md hover:bg-indigo-700 disabled:opacity-50">
          {{ loading ? '載入中...' : '查詢' }}
        </button>
        <div class="flex gap-2 flex-wrap">
          <button @click="setPreset('thisMonth')" class="px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300">本月</button>
          <button @click="setPreset('last3')" class="px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300">近3月</button>
          <button @click="setPreset('last6')" class="px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300">近6月</button>
          <button @click="setPreset('thisYear')" class="px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300">今年</button>
        </div>
      </div>
    </div>

    <div v-if="error" class="mt-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 text-red-700 dark:text-red-300 px-4 py-3 rounded-md text-sm">
      {{ error }}
    </div>

    <!-- Tab 切換：統計 / 趨勢 -->
    <div class="mt-6 border-b border-gray-200 dark:border-gray-700">
      <div class="flex">
        <button
          @click="activeTab = 'summary'"
          :class="['px-4 py-2 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'summary' ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400' : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300']"
        >支出分佈</button>
        <button
          @click="activeTab = 'trend'"
          :class="['px-4 py-2 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'trend' ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400' : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300']"
        >趨勢圖</button>
      </div>
    </div>

    <!-- 統計 Tab -->
    <div v-if="activeTab === 'summary' && summary" class="mt-6 space-y-6">
      <!-- 摘要卡片 -->
      <div class="grid grid-cols-3 gap-3">
        <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-4">
          <p class="text-xs text-gray-500 dark:text-gray-400">支出</p>
          <p class="mt-1 text-lg font-bold text-red-600 dark:text-red-400">${{ summary.expense_total.toLocaleString() }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-4">
          <p class="text-xs text-gray-500 dark:text-gray-400">收入</p>
          <p class="mt-1 text-lg font-bold text-green-600 dark:text-green-400">${{ summary.income_total.toLocaleString() }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-4">
          <p class="text-xs text-gray-500 dark:text-gray-400">損益</p>
          <p class="mt-1 text-lg font-bold" :class="summary.balance >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
            {{ summary.balance >= 0 ? '+' : '' }}${{ summary.balance.toLocaleString() }}
          </p>
        </div>
      </div>

      <!-- 圓餅圖 + 類別明細 -->
      <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
          <div v-if="chartData.length > 0" class="max-w-xs mx-auto">
            <PieChart :labels="chartLabels" :data="chartData" />
          </div>
          <p v-else class="text-center text-gray-500 dark:text-gray-400 py-8">無支出記錄</p>
        </div>
        <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
          <div class="space-y-3">
            <div v-for="cat in summary.categories" :key="cat.type" class="flex items-center justify-between">
              <span class="text-sm text-gray-700 dark:text-gray-300">{{ getCategoryName(cat.type) }}</span>
              <div class="text-right">
                <span class="text-sm font-medium text-gray-900 dark:text-gray-100">${{ cat.total.toLocaleString() }}</span>
                <span class="ml-2 text-xs text-gray-500 dark:text-gray-400">({{ cat.percentage }}%)</span>
              </div>
            </div>
          </div>
          <p class="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400">共 {{ summary.record_count }} 筆記錄</p>
        </div>
      </div>
    </div>

    <!-- 趨勢 Tab -->
    <div v-if="activeTab === 'trend' && trendData" class="mt-6 space-y-6">
      <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-4 sm:p-6">
        <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">支出/收入趨勢</h3>
        <div class="relative w-full" style="min-height: 200px;">
          <canvas ref="trendChartRef"></canvas>
        </div>
      </div>
      <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-4 sm:p-6">
        <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">各類別支出趨勢</h3>
        <div class="relative w-full" style="min-height: 200px;">
          <canvas ref="categoryTrendRef"></canvas>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { Chart, LineElement, PointElement, LineController, CategoryScale, LinearScale, Tooltip, Legend, Filler } from 'chart.js'
import { accountsApi } from '../api/accounts'
import { categoriesApi } from '../api/categories'
import PieChart from '../components/PieChart.vue'

Chart.register(LineElement, PointElement, LineController, CategoryScale, LinearScale, Tooltip, Legend, Filler)

// 從 API 載入類別
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

async function loadCategories() {
  try {
    const result = await categoriesApi.getCategories()
    categoriesList.value = result.categories
  } catch (err) {
    // 使用預設
  }
}

const COLORS = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#C9CBCF', '#7BC8A4', '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']

const activeTab = ref('summary')
const loading = ref(false)
const error = ref(null)
const summary = ref(null)
const trendData = ref(null)
const trendChartRef = ref(null)
const categoryTrendRef = ref(null)

let trendChartInstance = null
let categoryTrendInstance = null

// 使用 UTC+8 取得今天日期
function getTodayUTC8() {
  const now = new Date()
  const utc8Offset = 8 * 60
  const localOffset = now.getTimezoneOffset()
  return new Date(now.getTime() + (utc8Offset + localOffset) * 60 * 1000)
}

function formatDate(d) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${dd}`
}

const today = getTodayUTC8()
const startDate = ref(`${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-01`)
const endDate = ref(formatDate(today))

function getCategoryName(typeId) {
  return categoriesList.value.find(c => c.id === typeId)?.name || `類別${typeId}`
}

const chartLabels = computed(() => summary.value?.categories.map(c => getCategoryName(c.type)) || [])
const chartData = computed(() => summary.value?.categories.map(c => c.total) || [])

function setPreset(preset) {
  const now = getTodayUTC8()
  const y = now.getFullYear()
  const m = now.getMonth() + 1

  switch (preset) {
    case 'thisMonth':
      startDate.value = `${y}-${String(m).padStart(2, '0')}-01`
      endDate.value = formatDate(now)
      break
    case 'last3': {
      const s = new Date(y, m - 3, 1)
      startDate.value = formatDate(s)
      endDate.value = formatDate(now)
      break
    }
    case 'last6': {
      const s = new Date(y, m - 6, 1)
      startDate.value = formatDate(s)
      endDate.value = formatDate(now)
      break
    }
    case 'thisYear':
      startDate.value = `${y}-01-01`
      endDate.value = formatDate(now)
      break
  }
  loadData()
}

async function loadData() {
  loading.value = true
  error.value = null
  const sd = startDate.value.replace(/-/g, '_')
  const ed = endDate.value.replace(/-/g, '_')

  try {
    // 載入統計
    summary.value = await accountsApi.getSummaryRange(sd, ed)

    // 載入趨勢
    const startMonth = sd.substring(0, 7)
    const endMonth = ed.substring(0, 7)
    trendData.value = await accountsApi.getTrend(startMonth, endMonth)

    await nextTick()
    if (activeTab.value === 'trend') {
      renderTrendCharts()
    }
  } catch (err) {
    error.value = err.message || '載入失敗'
  } finally {
    loading.value = false
  }
}

watch(activeTab, async (val) => {
  if (val === 'trend' && trendData.value) {
    await nextTick()
    renderTrendCharts()
  }
})

function renderTrendCharts() {
  if (!trendData.value || !trendChartRef.value) return

  const labels = trendData.value.months.map(m => m.replace('_', '/'))
  const data = trendData.value.data

  const isDark = document.documentElement.classList.contains('dark')
  const gridColor = isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'
  const textColor = isDark ? '#d1d5db' : '#374151'

  // 總額趨勢圖
  if (trendChartInstance) trendChartInstance.destroy()
  trendChartInstance = new Chart(trendChartRef.value, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: '支出',
          data: data.map(d => d.expense_total),
          borderColor: '#EF4444',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          fill: true,
          tension: 0.3,
        },
        {
          label: '收入',
          data: data.map(d => d.income_total),
          borderColor: '#10B981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          fill: true,
          tension: 0.3,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      aspectRatio: window.innerWidth < 640 ? 1.2 : 2,
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: textColor, boxWidth: 12, padding: 8, font: { size: 11 } },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: gridColor },
          ticks: { color: textColor, font: { size: 10 } },
        },
        x: {
          grid: { color: gridColor },
          ticks: { color: textColor, font: { size: 10 }, maxRotation: 45 },
        },
      },
    },
  })

  // 類別趨勢圖
  if (!categoryTrendRef.value) return
  if (categoryTrendInstance) categoryTrendInstance.destroy()

  // 找出有資料的類別
  const activeCats = new Set()
  data.forEach(d => Object.keys(d.categories).forEach(k => activeCats.add(parseInt(k))))

  const datasets = [...activeCats]
    .filter(id => id !== 11)
    .sort((a, b) => a - b)
    .map((catId, idx) => ({
      label: getCategoryName(catId),
      data: data.map(d => d.categories[catId] || 0),
      borderColor: COLORS[idx % COLORS.length],
      tension: 0.3,
      pointRadius: window.innerWidth < 640 ? 2 : 3,
      borderWidth: window.innerWidth < 640 ? 1.5 : 2,
    }))

  categoryTrendInstance = new Chart(categoryTrendRef.value, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      aspectRatio: window.innerWidth < 640 ? 1.2 : 2,
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: textColor, boxWidth: 10, padding: 6, font: { size: 10 } },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: gridColor },
          ticks: { color: textColor, font: { size: 10 } },
        },
        x: {
          grid: { color: gridColor },
          ticks: { color: textColor, font: { size: 10 }, maxRotation: 45 },
        },
      },
    },
  })
}

onMounted(() => {
  loadCategories()
  loadData()
})
</script>
