<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-900">新增記帳</h2>

    <!-- 成功訊息 -->
    <div v-if="successMsg" class="mt-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-md text-sm">
      {{ successMsg }}
    </div>

    <!-- 錯誤訊息 -->
    <div v-if="error" class="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
      {{ error }}
    </div>

    <!-- 記帳表單 -->
    <form @submit.prevent="handleSubmit" class="mt-6 bg-white shadow rounded-lg p-6 space-y-4 max-w-lg">
      <div>
        <label for="name" class="block text-sm font-medium text-gray-700">項目名稱</label>
        <input
          id="name"
          v-model="form.name"
          type="text"
          required
          class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          placeholder="例：午餐、電費"
        />
      </div>

      <div>
        <label for="amount" class="block text-sm font-medium text-gray-700">金額</label>
        <input
          id="amount"
          v-model.number="form.amount"
          type="number"
          step="0.01"
          min="0.01"
          required
          class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          placeholder="輸入金額"
        />
      </div>

      <div>
        <label for="type" class="block text-sm font-medium text-gray-700">類別</label>
        <select
          id="type"
          v-model.number="form.type"
          required
          class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
        >
          <option value="" disabled>選擇類別</option>
          <option v-for="cat in categories" :key="cat.id" :value="cat.id">
            {{ cat.name }}
          </option>
        </select>
      </div>

      <div>
        <label for="date" class="block text-sm font-medium text-gray-700">日期</label>
        <input
          id="date"
          v-model="formDateDisplay"
          type="date"
          required
          class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
        />
      </div>

      <button
        type="submit"
        :disabled="submitting"
        class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
      >
        {{ submitting ? '送出中...' : '新增記帳' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAccountStore } from '../stores/accounts'

const accountStore = useAccountStore()

// 預設類別（Unit 5 會改為從 API 取得）
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

const form = ref({
  name: '',
  amount: null,
  type: '',
})

// 日期處理：HTML date input 用 YYYY-MM-DD，API 用 YYYY_MM_DD
const formDateDisplay = ref(new Date().toISOString().split('T')[0])

const submitting = ref(false)
const error = ref(null)
const successMsg = ref(null)

const formDate = computed(() => {
  return formDateDisplay.value.replace(/-/g, '_')
})

async function handleSubmit() {
  error.value = null
  successMsg.value = null
  submitting.value = true

  try {
    await accountStore.createAccount({
      name: form.value.name,
      amount: form.value.amount,
      type: form.value.type,
      date: formDate.value,
    })

    const catName = categories.find(c => c.id === form.value.type)?.name || ''
    successMsg.value = `✓ ${form.value.name} $${form.value.amount} (${catName}) 新增成功`

    // 清空表單（保留日期和類別）
    form.value.name = ''
    form.value.amount = null
  } catch (err) {
    error.value = err.message || '新增失敗'
  } finally {
    submitting.value = false
  }
}
</script>
