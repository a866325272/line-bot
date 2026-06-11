<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-900 dark:text-gray-100">個人設定</h2>

    <div v-if="error" class="mt-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 text-red-700 dark:text-red-300 px-4 py-3 rounded-md text-sm">
      {{ error }}
    </div>
    <div v-if="success" class="mt-4 bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-700 text-green-700 dark:text-green-300 px-4 py-3 rounded-md text-sm">
      {{ success }}
    </div>

    <div class="mt-6 bg-white dark:bg-gray-800 shadow rounded-lg p-6 max-w-lg space-y-6">
      <!-- Firestore Document ID (唯讀) -->
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">Firestore Document ID</label>
        <input
          :value="settings.firestore_doc_id"
          type="text"
          disabled
          class="mt-1 block w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-md bg-gray-50 dark:bg-gray-700 text-gray-500 dark:text-gray-400 sm:text-sm"
        />
        <p class="mt-1 text-xs text-gray-400 dark:text-gray-500">此為你的記帳資料 Document ID，無法修改</p>
      </div>

      <!-- Spreadsheet ID -->
      <div>
        <label for="spreadsheet-id" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Google Spreadsheet ID
        </label>
        <input
          id="spreadsheet-id"
          v-model="settings.spreadsheet_id"
          type="text"
          placeholder="例：1yUd_x3r0Jv1dm90p8BZIYQxRkgwm2Rrp6ZAduHG2YDY"
          class="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
        />
        <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
          從 Google Spreadsheet URL 中取得：
          <code class="bg-gray-100 dark:bg-gray-700 px-1 rounded">https://docs.google.com/spreadsheets/d/<strong>{這段就是 ID}</strong>/edit</code>
        </p>
      </div>

      <!-- 儲存按鈕 -->
      <button
        @click="handleSave"
        :disabled="saving"
        class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
      >
        {{ saving ? '儲存中...' : '儲存設定' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { settingsApi } from '../api/settings'

const settings = ref({
  firestore_doc_id: '',
  spreadsheet_id: '',
})
const error = ref(null)
const success = ref(null)
const saving = ref(false)

async function loadSettings() {
  try {
    const result = await settingsApi.getSettings()
    settings.value = result
  } catch (err) {
    error.value = err.message
  }
}

async function handleSave() {
  error.value = null
  success.value = null
  saving.value = true
  try {
    await settingsApi.updateSettings({
      spreadsheet_id: settings.value.spreadsheet_id,
    })
    success.value = '設定已儲存'
    setTimeout(() => { success.value = null }, 3000)
  } catch (err) {
    error.value = err.message
  } finally {
    saving.value = false
  }
}

onMounted(loadSettings)
</script>
