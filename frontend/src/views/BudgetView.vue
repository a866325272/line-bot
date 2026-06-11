<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-900 dark:text-gray-100">預算設定</h2>

    <div v-if="error" class="mt-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 text-red-700 dark:text-red-300 px-4 py-3 rounded-md text-sm">
      {{ error }}
    </div>
    <div v-if="success" class="mt-4 bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-700 text-green-700 dark:text-green-300 px-4 py-3 rounded-md text-sm">
      {{ success }}
    </div>

    <!-- 預算設定表格 -->
    <div class="mt-6 bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead class="bg-gray-50 dark:bg-gray-700">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">類別</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">月預算</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">本月已花</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">使用率</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
          <tr v-for="item in budgetItems" :key="item.id" class="hover:bg-gray-50 dark:hover:bg-gray-700">
            <td class="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">{{ item.name }}</td>
            <td class="px-4 py-3 text-sm">
              <input
                v-model.number="item.budget"
                type="number"
                min="0"
                step="100"
                class="w-24 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded text-sm focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                @change="saveBudget(item)"
              />
            </td>
            <td class="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">
              ${{ (item.spent || 0).toLocaleString() }}
            </td>
            <td class="px-4 py-3 text-sm">
              <div v-if="item.budget > 0" class="flex items-center space-x-2">
                <div class="flex-1 bg-gray-200 dark:bg-gray-600 rounded-full h-2 max-w-[100px]">
                  <div
                    class="h-2 rounded-full transition-all"
                    :class="item.over ? 'bg-red-500' : 'bg-green-500'"
                    :style="{ width: Math.min(item.percentage, 100) + '%' }"
                  ></div>
                </div>
                <span :class="item.over ? 'text-red-600 dark:text-red-400 font-medium' : 'text-gray-600 dark:text-gray-400'" class="text-xs">
                  {{ item.percentage }}%
                </span>
              </div>
              <span v-else class="text-xs text-gray-400 dark:text-gray-500">未設定</span>
            </td>
            <td class="px-4 py-3 text-right text-sm">
              <button
                v-if="item.budget > 0"
                @click="clearBudget(item)"
                class="text-gray-500 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 text-xs"
              >
                清除
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { categoriesApi } from '../api/categories'
import { budgetApi } from '../api/budget'

const error = ref(null)
const success = ref(null)
const budgetItems = ref([])

async function loadData() {
  try {
    const [catResult, budgetResult, statusResult] = await Promise.all([
      categoriesApi.getCategories(),
      budgetApi.getBudgets(),
      budgetApi.getBudgetStatus(),
    ])

    const categories = catResult.categories.filter(c => c.id !== 11)
    const budgets = budgetResult.budgets
    const statusList = statusResult.status

    budgetItems.value = categories.map(cat => {
      const status = statusList.find(s => s.category_id === cat.id)
      return {
        id: cat.id,
        name: cat.name,
        budget: budgets[String(cat.id)] || 0,
        spent: status?.spent || 0,
        percentage: status?.percentage || 0,
        over: status?.over || false,
      }
    })
  } catch (err) {
    error.value = err.message
  }
}

async function saveBudget(item) {
  error.value = null
  success.value = null
  try {
    await budgetApi.setBudget(item.id, item.budget)
    success.value = `${item.name} 預算已更新為 $${item.budget}`
    await loadData()
    setTimeout(() => { success.value = null }, 3000)
  } catch (err) {
    error.value = err.message
  }
}

async function clearBudget(item) {
  item.budget = 0
  await saveBudget(item)
}

onMounted(loadData)
</script>
