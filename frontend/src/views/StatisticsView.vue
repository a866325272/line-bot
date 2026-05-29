<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-900">統計與趨勢</h2>

    <!-- 日期區間選擇 -->
    <div class="mt-4 bg-white shadow rounded-lg p-4">
      <div class="flex flex-wrap items-end gap-3">
        <div>
          <label class="block text-xs font-medium text-gray-500">起始日期</label>
          <input v-model="startDate" type="date"
            class="mt-1 px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500" />
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500">結束日期</label>
          <input v-model="endDate" type="date"
            class="mt-1 px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500" />
        </div>
        <button @click="loadData" :disabled="loading"
          class="px-4 py-1.5 bg-indigo-600 text-white text-sm rounded-md hover:bg-indigo-700 disabled:opacity-50">
          {{ loading ? '載入中...' : '查詢' }}
        </button>
        <div class="flex gap-2">
          <button @click="setPreset('thisMonth')" class="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50">本月</button>
          <button @click="setPreset('last3')" class="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50">近3月</button>
          <button @click="setPreset('last6')" class="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50">近6月</button>
          <button @click="setPreset('thisYear')" class="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50">今年</button>
        </div>
      </div>
    </div>

    <div v-if="error" class="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
      {{ error }}
    </div>

    <!-- Tab 切換：統計 / 趨勢 -->
    <div class="mt-6 border-b border-gray-200">
      <div class="flex">
        <button
          @click="activeTab = 'summary'"
          :class="['px-4 py-2 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'summary' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700']"
        >支出分佈</button>
        <button
          @click="activeTab = 'trend'"
          :class="['px-4 py-2 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'trend' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700']"
        >趨勢圖</button>
      </div>
    </div>

    <!-- 統計 Tab -->
    <div v-if="activeTab === 'summary' && summary" class="mt-6 space-y-6">
      <!-- 摘要卡片 -->
      <div class="grid grid-cols-3 gap-3">
        <div class="bg-white shadow rounded-lg p-4">
          <p class="text-xs text-gray-500">支出</p>
          <p class="mt-1 text-lg font-bold text-red-600">${{ summary.expense_total.toLocaleString() }}</p>
        </div>
        <div class="bg-white shadow rounded-lg p-4">
          <p class="text-xs text-gray-500">收入</p>
          <p class="mt-1 text-lg font-bold text-green-600">${{ summary.income_total.toLocaleString() }}</p>
        </div>
        <div class="bg-white shadow rounded-lg p-4">
          <p class="text-xs text-gray-500">損益</p>
          <p class="mt-1 text-lg font-bold" :class="summary.balance >= 0 ? 'text-green-600' : 'text-red-600'">
            {{ summary.balance >= 0 ? '+' : '' }}${{ summary.balance.toLocaleString() }}
          </p>
        </div>
      </div>

      <!-- 圓餅圖 + 類別明細 -->
      <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div class="bg-white shadow rounded-lg p-6">
          <div v-if="chartData.length > 0" class="max-w-xs mx-auto">
            <PieChart :labels="chartLabels" :data="chartData" />
          </div>
          <p v-else class="text-center text-gray-500 py-8">無支出記錄</p>
        </div>
        <div class="bg-white shadow rounded-lg p-6">
          <div class="space-y-3">
            <div v-for="cat in summary.categories" :key="cat.type" class="flex items-center justify-between">
              <span class="text-sm text-gray-700">{{ getCategoryName(cat.type) }}</span>
              <div class="text-right">
                <span class="text-sm font-medium">${{ cat.total.toLocaleString() }}</span>
                <span class="ml-2 text-xs text-gray-500">({{ cat.percentage }}%)</span>
              </div>
            </div>
          </div>
          <p class="mt-4 pt-3 border-t text-xs text-gray-500">共 {{ summary.record_count }} 筆記錄</p>
        </div>
      </div>
    </div>

    <!-- 趨勢 Tab -->
    <div v-if="activeTab === 'trend' && trendData" class="mt-6 space-y-6">
      <div class="bg-white shadow rounded-lg p-6">
        <h3 class="text-sm font-medium text-gray-700 mb-4">支出/收入趨勢</h3>
        <canvas ref="trendChartRef"></canvas>
      </div>
      <div class="bg-white shadow rounded-lg p-6">
        <h3 class="text-sm font-medium text-gray-700 mb-4">各類別支出趨勢</h3>
        <canvas ref="categoryTrendRef"></canvas>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { Chart, LineElement, PointElement, LineController, CategoryScale, LinearScale, Tooltip, Legend, Filler } from 'chart.js'
import { accountsApi } from '../api/accounts'
import PieChart from '../components/PieChart.vue'

Chart.register(LineElement, PointElement, LineController, CategoryScale, LinearScale, Tooltip, Legend, Filler)

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

const COLORS = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#C9CBCF', '#7BC8A4']

const activeTab = ref('summary')
const loading = ref(false)
const error = ref(null)
const summary = ref(null)
const trendData = ref(null)
const trendChartRef = ref(null)
const categoryTrendRef = ref(null)

let trendChartInstance = null
let categoryTrendInstance = null

// 預設日期：本月
const now = new Date()
const startDate = ref(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-01`)
const endDate = ref(now.toISOString().split('T')[0])

function getCategoryName(typeId) {
  return categories.find(c => c.id === typeId)?.name || `類別${typeId}`
}

const chartLabels = computed(() => summary.value?.categories.map(c => getCategoryName(c.type)) || [])
const chartData = computed(() => summary.value?.categories.map(c => c.total) || [])

function setPreset(preset) {
  const today = new Date()
  const y = today.getFullYear()
  const m = today.getMonth() + 1

  switch (preset) {
    case 'thisMonth':
      startDate.value = `${y}-${String(m).padStart(2, '0')}-01`
      endDate.value = today.toISOString().split('T')[0]
      break
    case 'last3': {
      const s = new Date(y, m - 3, 1)
      startDate.value = s.toISOString().split('T')[0]
      endDate.value = today.toISOString().split('T')[0]
      break
    }
    case 'last6': {
      const s = new Date(y, m - 6, 1)
      startDate.value = s.toISOString().split('T')[0]
      endDate.value = today.toISOString().split('T')[0]
      break
    }
    case 'thisYear':
      startDate.value = `${y}-01-01`
      endDate.value = today.toISOString().split('T')[0]
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
      plugins: { legend: { position: 'bottom' } },
      scales: { y: { beginAtZero: true } },
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
      pointRadius: 3,
    }))

  categoryTrendInstance = new Chart(categoryTrendRef.value, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      plugins: { legend: { position: 'bottom' } },
      scales: { y: { beginAtZero: true } },
    },
  })
}

onMounted(loadData)
</script>
