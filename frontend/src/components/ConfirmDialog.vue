<template>
  <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center">
    <!-- Overlay -->
    <div class="fixed inset-0 bg-black bg-opacity-50" @click="$emit('cancel')"></div>

    <!-- Dialog -->
    <div class="relative bg-white rounded-lg shadow-xl max-w-sm w-full mx-4 p-6">
      <h3 class="text-lg font-medium text-gray-900">{{ title }}</h3>
      <p class="mt-2 text-sm text-gray-500">{{ message }}</p>

      <div class="mt-4 flex justify-end space-x-3">
        <button
          @click="$emit('cancel')"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          取消
        </button>
        <button
          @click="$emit('confirm')"
          class="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700"
        >
          {{ confirmText }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  show: { type: Boolean, default: false },
  title: { type: String, default: '確認' },
  message: { type: String, default: '確定要執行此操作嗎？' },
  confirmText: { type: String, default: '確定' },
})

defineEmits(['confirm', 'cancel'])
</script>
