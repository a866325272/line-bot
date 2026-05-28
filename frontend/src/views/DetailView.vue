<template>
  <div>
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-bold text-gray-900">明細列表</h2>

      <div class="flex items-center space-x-4">
        <!-- 匯出按鈕 -->
        <button
          @click="handleExport"
          :disabled="exporting || accountStore.accounts.length === 0"
          class="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ exporting ? '匯出中...' : '📤 匯出到 Spreadsheet' }}
        </button>

        <!-- 月份選擇 -->
        <div class="flex items-center space-x-2">
          <button @click="prevMonth" class="p-1 rounded hover:bg-gray-100">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <span class="text-sm font-medium text-gray-700 min-w-[80px] text-center">
            {{ displayMonth }}
          </span>
          <button @click="nextMonth" class="p-1 rounded hover:bg-gray-100">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- 匯出成功訊息 -->
    <div v-if="exportUrl" class="mt-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-md text-sm">
      匯出成功！<a :href="exportUrl" target="_blank" class="underline font-medium">點此開啟 Spreadsheet</a>
    </div>

    <!-- 錯誤訊息 -->
    <div v-if="error" class="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
      {{ error }}
    </div>

    <!-- 表格 -->
    <div class="mt-6 bg-white shadow rounded-lg overflow-hidden">
      <DataTable :columns="columns" :data="accountStore.accounts" empty-text="本月沒有記帳記錄">
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
          <button
            @click="startEdit(row)"
            class="text-indigo-600 hover:text-indigo-900 mr-3 text-sm"
          >
            編輯
          </button>
          <button
            @click="confirmDelete(row)"
            class="text-red-600 hover:text-red-900 text-sm"
          >
            刪除
          </button>
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
              class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">
              取消
            </button>
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
      :message="`確定要刪除「${deletingRow?.name}」$${deletingRow?.amount} 嗎？此操作無法復原。`"
      confirm-text="刪除"
      @confirm="handleDelete"
      @cancel="deletingRow = null"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useAccountStore } from '../stores/accounts'
import { exportApi } from '../api/export'
import DataTable from '../components/DataTable.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'

const accountStore = useAccountStore()

const error = ref(null)
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

const displayMonth = computed(() => {
  const parts = accountStore.currentMonth.split('_')
  return `${parts[0]}/${parts[1]}`
})

function getCategoryName(typeId) {
  return categories.find(c => c.id === typeId)?.name || `類別${typeId}`
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return dateStr.replace(/_/g, '/')
}

function prevMonth() {
  const parts = accountStore.currentMonth.split('_')
  let year = parseInt(parts[0])
  let month = parseInt(parts[1]) - 1
  if (month < 1) { month = 12; year-- }
  accountStore.setMonth(`${year}_${String(month).padStart(2, '0')}`)
  loadData()
}

function nextMonth() {
  const parts = accountStore.currentMonth.split('_')
  let year = parseInt(parts[0])
  let month = parseInt(parts[1]) + 1
  if (month > 12) { month = 1; year++ }
  accountStore.setMonth(`${year}_${String(month).padStart(2, '0')}`)
  loadData()
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
    await accountStore.updateAccount(accountStore.currentMonth, editingRow.value.index, {
      name: editForm.value.name,
      amount: editForm.value.amount,
      type: editForm.value.type,
      date: editForm.value.date.replace(/-/g, '_'),
    })
    editingRow.value = null
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
    await accountStore.deleteAccount(accountStore.currentMonth, deletingRow.value.index)
    deletingRow.value = null
  } catch (err) {
    error.value = err.message || '刪除失敗'
  }
}

async function handleExport() {
  exporting.value = true
  exportUrl.value = null
  error.value = null
  try {
    const result = await exportApi.exportToSpreadsheet(accountStore.currentMonth)
    exportUrl.value = result.sheet_url
  } catch (err) {
    error.value = err.message || '匯出失敗'
  } finally {
    exporting.value = false
  }
}

async function loadData() {
  error.value = null
  try {
    await accountStore.fetchAccounts()
  } catch (err) {
    error.value = err.message || '載入失敗'
  }
}

onMounted(loadData)
</script>
