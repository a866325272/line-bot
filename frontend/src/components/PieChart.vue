<template>
  <div class="relative">
    <canvas ref="chartRef"></canvas>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { Chart, ArcElement, Tooltip, Legend, PieController } from 'chart.js'

Chart.register(ArcElement, Tooltip, Legend, PieController)

const props = defineProps({
  labels: { type: Array, default: () => [] },
  data: { type: Array, default: () => [] },
  title: { type: String, default: '' },
})

const chartRef = ref(null)
let chartInstance = null

const COLORS = [
  '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
  '#9966FF', '#FF9F40', '#C9CBCF', '#7BC8A4',
]

function renderChart() {
  if (chartInstance) {
    chartInstance.destroy()
  }

  if (!chartRef.value || props.data.length === 0) return

  const ctx = chartRef.value.getContext('2d')

  // 過濾掉 0 值
  const filteredData = []
  const filteredLabels = []
  const filteredColors = []

  props.data.forEach((value, index) => {
    if (value > 0) {
      filteredData.push(value)
      filteredLabels.push(props.labels[index] || `類別${index}`)
      filteredColors.push(COLORS[index % COLORS.length])
    }
  })

  if (filteredData.length === 0) return

  chartInstance = new Chart(ctx, {
    type: 'pie',
    data: {
      labels: filteredLabels,
      datasets: [{
        data: filteredData,
        backgroundColor: filteredColors,
        borderWidth: 2,
        borderColor: '#fff',
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            padding: 16,
            usePointStyle: true,
          },
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              const total = context.dataset.data.reduce((a, b) => a + b, 0)
              const value = context.parsed
              const percentage = ((value / total) * 100).toFixed(1)
              return `${context.label}: $${value} (${percentage}%)`
            },
          },
        },
        title: {
          display: !!props.title,
          text: props.title,
          font: { size: 16 },
        },
      },
    },
  })
}

onMounted(renderChart)

watch(() => [props.data, props.labels], renderChart, { deep: true })

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy()
  }
})
</script>
