<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-900">明細列表</h2>

    <!-- 日期區間選擇 + 匯出 -->
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
          查詢
        </button>
        <div class="flex gap-2">
          <button @click="setPreset('thisMonth')" class="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50">本月</button>
          <button @click="setPreset('lastMonth')" class="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50">上月</button>
          <button @click="setPreset('last3')" class="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50">近3月</button>
        </div>

        <!-- 匯出（按月匯出） -->
        <div class="ml-auto">
          <div class="flex items-center gap-2">
            <select v-model="exportMonth" class="px-2 py-1.5 border border-gray-300 rounded-md text-sm">
              <option v-for="m in availableMonths" :key="m" :value="m">{{ m.replace('_', '/') }}</option>
            </select>
            <button
              @click="handleExport"
              :disabled="exporting"
              class="px-3 py-1.5 border border-gray-300 text-sm rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
            >
              {{ exporting ? '匯出中...' : '📤 匯出' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 匯出成功 -->
    <div v-if="exportUrl" class="mt-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-md text-sm">
      匯出成功！<a :href="exportUrl" target="_blank" class="underline font-medium">點此開啟 Spreadsheet</a>
    </div>

    <!-- 錯誤 -->
    <div v-if="error" class="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
      {{ error }}
    </div>

    <!-- 記錄數 -->
    <p class="mt-4 text-sm text-gray-500">共 {{ accounts.length }} 筆記錄</p>

    <!-- 表格 -->
    <div class="mt-2 bg-white shadow rounded-lg overflow-hidden">
      <DataTable :columns="columns" :data="accounts" empty-text="此區間沒有記帳記錄">
        <template #cell-type="{ value }">
          <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
                :class="value === 11 ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'">
            {{ getCategoryName(value) }}
          </span>
        </template>
        <template #cell-amount="{ row }">
          <span :class="row.type === 11 ? 'text-green-600' : 'text-red-600'">
            {{ row.type === 11 ? '+' : '-' }}${{ row.amount }}
          </span>
        </template>
        <template #cell-date="{ value }">
          {{ formatDate(value) }}
        </template>
        <template #actions="{ row }">
          <button @click="startEdit(row)" class="text-indigo-600 hover:text-indigo-900 mr-3 text-sm">編輯</button>
          <button @click="confirmDelete(row)" class="text-red-600 hover:text-red-900 text-sm">刪除</button>
        </template>
      </DataTable>
    </div>

    <!-- 編輯 Modal -->
    <div v-if="editingRow" class="fixed inset-0 z-50 flex items-center justify-center">
      <div class="fixed inset-0 bg-black bg-opacity-50" @click="editingRow = null"></div>
      <div class="relative bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
        <h3 class="text-lg font-medium text-gray-900">編輯記錄</h3>
        <form @submit.prevent="handleUpdate" class="mt-4 space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">項目名稱</label>
            <input v-model="editForm.name" type="text" required
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">金額</label>
            <input v-model.number="editForm.amount" type="number" step="0.01" min="0.01" required
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">類別</label>
            <select v-model.number="editForm.type" required
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm">
              <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">日期</label>
            <input v-model="editForm.date" type="date" required
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
          </div>
          <div class="flex justify-end space-x-3">
            <button type="button" @click="editingRow = null"
              class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">取消</button>
            <button type="submit" :disabled="saving"
              class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50">
              {{ saving ? '儲存中...' : '儲存' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 刪除確認 -->
    <ConfirmDialog
      :show="!!deletingRow"
      title="刪除記錄"
      :message="`確定要刪除「${deletingRow?.name}」$${deletingRow?.amount} 嗎？`"
      confirm-text="刪除"
      @confirm="handleDelete"
      @cancel="deletingRow = null"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { accountsApi } from '../api/accounts'
import { exportApi } from '../api/export'
import DataTable from '../components/DataTable.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'

const error = ref(null)
const loading = ref(false)
const accounts = ref([])
const editingRow = ref(null)
const deletingRow = ref(null)
const saving = ref(false)
const editForm = ref({ name: '', amount: 0, type: 1, date: '' })
const exporting = ref(false)
const exportUrl = ref(null)

const categories = [
  { id: 1, name: '飲食' },
  { id: 2, name: '生活' },
  { id: 3, name: '居住' },
  { id: 4, name: '交通' },
  { id: 5, name: '娛樂' },
  { id: 6, name: '醫療' },
  { id: 7, name: '其他' },
  { id: 8, name: '投資' },
  { id: 11, name: '收入' },
]

const columns = [
  { key: 'date', label: '日期' },
  { key: 'name', label: '項目' },
  { key: 'amount', label: '金額' },
  { key: 'type', label: '類別' },
]

// 預設日期：本月
const now = new Date()
const startDate = ref(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-01`)
const endDate = ref(now.toISOString().split('T')[0])

// 匯出用的月份選擇
const exportMonth = ref(`${now.getFullYear()}_${String(now.getMonth() + 1).padStart(2, '0')}`)

// 從查詢結果中提取可用月份（供匯出選擇）
const availableMonths = computed(() => {
  const months = new Set()
  accounts.value.forEach(acc => {
    if (acc.date) {
      const parts = acc.date.split('_')
      if (parts.length >= 2) months.add(`${parts[0]}_${parts[1]}`)
    }
  })
  return [...months].sort().reverse()
})

function getCategoryName(typeId) {
  return categories.find(c => c.id === typeId)?.name || `類別${typeId}`
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return dateStr.replace(/_/g, '/')
}

function setPreset(preset) {
  const today = new Date()
  const y = today.getFullYear()
  const m = today.getMonth() + 1

  switch (preset) {
    case 'thisMonth':
      startDate.value = `${y}-${String(m).padStart(2, '0')}-01`
      endDate.value = today.toISOString().split('T')[0]
      break
    case 'lastMonth': {
      const lm = m === 1 ? 12 : m - 1
      const ly = m === 1 ? y - 1 : y
      const lastDay = new Date(ly, lm, 0).getDate()
      startDate.value = `${ly}-${String(lm).padStart(2, '0')}-01`
      endDate.value = `${ly}-${String(lm).padStart(2, '0')}-${lastDay}`
      break
    }
    case 'last3': {
      const s = new Date(y, m - 3, 1)
      startDate.value = s.toISOString().split('T')[0]
      endDate.value = today.toISOString().split('T')[0]
      break
    }
  }
  loadData()
}

async function loadData() {
  loading.value = true
  error.value = null
  exportUrl.value = null
  try {
    const sd = startDate.value.replace(/-/g, '_')
    const ed = endDate.value.replace(/-/g, '_')
    const result = await accountsApi.getAccountsRange(sd, ed)
    accounts.value = result.accounts
    // 更新匯出月份為結果中最新的月份
    if (availableMonths.value.length > 0) {
      exportMonth.value = availableMonths.value[0]
    }
  } catch (err) {
    error.value = err.message || '載入失敗'
  } finally {
    loading.value = false
  }
}

function startEdit(row) {
  editingRow.value = row
  editForm.value = {
    name: row.name,
    amount: row.amount,
    type: row.type,
    date: row.date.replace(/_/g, '-'),
  }
}

async function handleUpdate() {
  saving.value = true
  error.value = null
  try {
    const month = editingRow.value.month || editingRow.value.date.substring(0, 7)
    await accountsApi.updateAccount(month, editingRow.value.index, {
      name: editForm.value.name,
      amount: editForm.value.amount,
      type: editForm.value.type,
      date: editForm.value.date.replace(/-/g, '_'),
    })
    editingRow.value = null
    await loadData()
  } catch (err) {
    error.value = err.message || '更新失敗'
  } finally {
    saving.value = false
  }
}

function confirmDelete(row) {
  deletingRow.value = row
}

async function handleDelete() {
  error.value = null
  try {
    const month = deletingRow.value.month || deletingRow.value.date.substring(0, 7)
    await accountsApi.deleteAccount(month, deletingRow.value.index)
    deletingRow.value = null
    await loadData()
  } catch (err) {
    error.value = err.message || '刪除失敗'
  }
}

async function handleExport() {
  exporting.value = true
  exportUrl.value = null
  error.value = null
  try {
    const result = await exportApi.exportToSpreadsheet(exportMonth.value)
    exportUrl.value = result.sheet_url
  } catch (err) {
    error.value = err.message || '匯出失敗'
  } finally {
    exporting.value = false
  }
}

onMounted(loadData)
</script>
