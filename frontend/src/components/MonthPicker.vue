<template>
  <div class="flex items-center space-x-2">
    <button
      @click="prev"
      class="p-1.5 rounded-md hover:bg-gray-100 text-gray-600 hover:text-gray-900"
      aria-label="上個月"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
    </button>
    <span class="text-sm font-medium text-gray-700 min-w-[80px] text-center">
      {{ displayText }}
    </span>
    <button
      @click="next"
      class="p-1.5 rounded-md hover:bg-gray-100 text-gray-600 hover:text-gray-900"
      aria-label="下個月"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
      </svg>
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /** 格式: YYYY_MM */
  modelValue: { type: String, required: true },
})

const emit = defineEmits(['update:modelValue'])

const displayText = computed(() => {
  const parts = props.modelValue.split('_')
  return `${parts[0]}/${parts[1]}`
})

function prev() {
  const parts = props.modelValue.split('_')
  let year = parseInt(parts[0])
  let month = parseInt(parts[1]) - 1
  if (month < 1) { month = 12; year-- }
  emit('update:modelValue', `${year}_${String(month).padStart(2, '0')}`)
}

function next() {
  const parts = props.modelValue.split('_')
  let year = parseInt(parts[0])
  let month = parseInt(parts[1]) + 1
  if (month > 12) { month = 1; year++ }
  emit('update:modelValue', `${year}_${String(month).padStart(2, '0')}`)
}
</script>
