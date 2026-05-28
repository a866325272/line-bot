<template>
  <div class="overflow-x-auto">
    <table class="min-w-full divide-y divide-gray-200">
      <thead class="bg-gray-50">
        <tr>
          <th
            v-for="col in columns"
            :key="col.key"
            class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
            @click="col.sortable !== false && toggleSort(col.key)"
          >
            <div class="flex items-center space-x-1">
              <span>{{ col.label }}</span>
              <span v-if="sortKey === col.key" class="text-indigo-600">
                {{ sortOrder === 'asc' ? '↑' : '↓' }}
              </span>
            </div>
          </th>
          <th v-if="$slots.actions" class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
            操作
          </th>
        </tr>
      </thead>
      <tbody class="bg-white divide-y divide-gray-200">
        <tr v-for="(row, idx) in sortedData" :key="idx" class="hover:bg-gray-50">
          <td v-for="col in columns" :key="col.key" class="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
            <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">
              {{ col.format ? col.format(row[col.key], row) : row[col.key] }}
            </slot>
          </td>
          <td v-if="$slots.actions" class="px-4 py-3 whitespace-nowrap text-right text-sm">
            <slot name="actions" :row="row" :index="idx"></slot>
          </td>
        </tr>
        <tr v-if="sortedData.length === 0">
          <td :colspan="columns.length + ($slots.actions ? 1 : 0)" class="px-4 py-8 text-center text-sm text-gray-500">
            {{ emptyText }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  columns: { type: Array, required: true },
  data: { type: Array, default: () => [] },
  emptyText: { type: String, default: '沒有資料' },
})

const sortKey = ref(null)
const sortOrder = ref('asc')

function toggleSort(key) {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortOrder.value = 'asc'
  }
}

const sortedData = computed(() => {
  if (!sortKey.value) return props.data

  return [...props.data].sort((a, b) => {
    const aVal = a[sortKey.value]
    const bVal = b[sortKey.value]

    if (aVal == null) return 1
    if (bVal == null) return -1

    let comparison = 0
    if (typeof aVal === 'number' && typeof bVal === 'number') {
      comparison = aVal - bVal
    } else {
      comparison = String(aVal).localeCompare(String(bVal))
    }

    return sortOrder.value === 'asc' ? comparison : -comparison
  })
})
</script>
