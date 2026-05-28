<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-900">類別管理</h2>

    <div v-if="error" class="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
      {{ error }}
    </div>

    <!-- 新增類別 -->
    <div class="mt-6 bg-white shadow rounded-lg p-6">
      <h3 class="text-lg font-medium text-gray-900 mb-4">新增類別</h3>
      <form @submit.prevent="handleCreate" class="flex items-end space-x-4">
        <div class="flex-1">
          <label class="block text-sm font-medium text-gray-700">類別名稱</label>
          <input v-model="newName" type="text" required placeholder="例：寵物"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
        </div>
        <div class="w-24">
          <label class="block text-sm font-medium text-gray-700">代號</label>
          <input v-model.number="newId" type="number" min="1" required placeholder="9"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
        </div>
        <button type="submit" :disabled="creating"
          class="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 disabled:opacity-50">
          新增
        </button>
      </form>
    </div>

    <!-- 類別列表 -->
    <div class="mt-6 bg-white shadow rounded-lg overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">代號</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">名稱</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">類型</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr v-for="cat in categories" :key="cat.id" class="hover:bg-gray-50">
            <td class="px-4 py-3 text-sm text-gray-900">{{ cat.id }}</td>
            <td class="px-4 py-3 text-sm text-gray-900">
              <span v-if="editingId !== cat.id">{{ cat.name }}</span>
              <input v-else v-model="editName" type="text"
                class="px-2 py-1 border border-gray-300 rounded text-sm w-32"
                @keyup.enter="handleUpdate(cat.id)"
                @keyup.escape="editingId = null" />
            </td>
            <td class="px-4 py-3 text-sm">
              <span :class="cat.is_default ? 'text-gray-500' : 'text-indigo-600'" class="text-xs">
                {{ cat.is_default ? '預設' : '自訂' }}
              </span>
            </td>
            <td class="px-4 py-3 text-right text-sm space-x-2">
              <template v-if="editingId === cat.id">
                <button @click="handleUpdate(cat.id)" class="text-green-600 hover:text-green-900">儲存</button>
                <button @click="editingId = null" class="text-gray-600 hover:text-gray-900">取消</button>
              </template>
              <template v-else>
                <button @click="startEdit(cat)" class="text-indigo-600 hover:text-indigo-900">編輯</button>
                <button v-if="!cat.is_default" @click="handleDelete(cat)" class="text-red-600 hover:text-red-900">刪除</button>
              </template>
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

const categories = ref([])
const error = ref(null)
const newName = ref('')
const newId = ref(null)
const creating = ref(false)
const editingId = ref(null)
const editName = ref('')

async function loadCategories() {
  try {
    const result = await categoriesApi.getCategories()
    categories.value = result.categories
  } catch (err) {
    error.value = err.message
  }
}

async function handleCreate() {
  error.value = null
  creating.value = true
  try {
    await categoriesApi.createCategory({ name: newName.value, id: newId.value })
    newName.value = ''
    newId.value = null
    await loadCategories()
  } catch (err) {
    error.value = err.message
  } finally {
    creating.value = false
  }
}

function startEdit(cat) {
  editingId.value = cat.id
  editName.value = cat.name
}

async function handleUpdate(id) {
  error.value = null
  try {
    await categoriesApi.updateCategory(id, { name: editName.value })
    editingId.value = null
    await loadCategories()
  } catch (err) {
    error.value = err.message
  }
}

async function handleDelete(cat) {
  if (!confirm(`確定要刪除「${cat.name}」嗎？`)) return
  error.value = null
  try {
    await categoriesApi.deleteCategory(cat.id)
    await loadCategories()
  } catch (err) {
    error.value = err.message
  }
}

onMounted(loadCategories)
</script>
