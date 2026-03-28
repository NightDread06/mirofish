<template>
  <div class="crowd-heatmap">
    <div class="chart-title">👥 Crowd Heatmap (Runs × Hours)</div>

    <div v-if="loading" class="loading">Loading crowd data…</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <template v-else-if="matrix.length">
      <div class="heatmap-scroll">
        <table class="heatmap-table">
          <thead>
            <tr>
              <th class="run-col">Run</th>
              <th v-for="h in hours" :key="h" class="hour-col">{{ h }}h</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in matrix" :key="row.name">
              <td class="run-name-cell">{{ row.name }}</td>
              <td
                v-for="(val, idx) in row.values"
                :key="idx"
                class="heat-cell"
                :style="{ background: heatColor(val) }"
                :title="`${row.name} @ ${hours[idx]}:00 — ${crowdLabel(val)}`"
              >
                <span class="cell-val">{{ crowdShort(val) }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="legend">
        <div v-for="item in legendItems" :key="item.label" class="legend-item">
          <span class="legend-swatch" :style="{ background: item.color }"></span>
          {{ item.label }}
        </div>
      </div>
    </template>

    <div v-else class="empty">No crowd data available.</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getRecommendations } from '../../../api/ski.js'

const matrix = ref([])
const loading = ref(true)
const error = ref(null)

const hours = [9, 10, 11, 12, 13, 14, 15, 16]

const legendItems = [
  { label: 'Low',    color: '#c6f6d5' },
  { label: 'Medium', color: '#fefcbf' },
  { label: 'High',   color: '#fed7d7' },
]

function heatColor(val) {
  // val is crowd_level 0–1
  if (val < 0.33) return '#c6f6d5'   // low – green
  if (val < 0.66) return '#fefcbf'   // medium – yellow
  return '#fed7d7'                    // high – red
}

function crowdLabel(val) {
  if (val < 0.33) return 'Low'
  if (val < 0.66) return 'Medium'
  return 'High'
}

function crowdShort(val) {
  if (val < 0.33) return 'L'
  if (val < 0.66) return 'M'
  return 'H'
}

// Build matrix by fetching recommendations at different simulated hours.
// We use a simplified crowd model based on known hourly patterns.
const HOUR_CROWD = {
  9: 0.72, 10: 0.95, 11: 1.00, 12: 0.62,
  13: 0.55, 14: 0.90, 15: 0.82, 16: 0.50,
}

async function load() {
  loading.value = true
  error.value = null
  try {
    // Fetch current recommendations to get run list + base crowd levels
    const data = await getRecommendations()
    const runs = data.runs || []

    matrix.value = runs.map(run => ({
      name: run.name,
      values: hours.map(h => {
        const base = run.crowd_level
        const hourMod = HOUR_CROWD[h] ?? 0.7
        return Math.min(1, base * hourMod * 1.3)
      }),
    }))
  } catch (e) {
    error.value = 'Could not build crowd heatmap.'
  } finally {
    loading.value = false
  }
}

const REFRESH_MS = 10 * 60 * 1000
let timer = null
onMounted(() => {
  load()
  timer = setInterval(load, REFRESH_MS)
})
onUnmounted(() => clearInterval(timer))

defineExpose({ refresh: load })
</script>

<style scoped>
.crowd-heatmap {
  background: #fff;
  border: 1px solid #e5e5e5;
  padding: 20px;
}

.chart-title {
  font-weight: 700;
  font-size: 1rem;
  margin-bottom: 14px;
}

.loading, .error, .empty {
  padding: 20px 0;
  font-size: 0.9rem;
  color: #999;
}
.error { color: #e53e3e; }

.heatmap-scroll { overflow-x: auto; }

.heatmap-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.78rem;
}

.heatmap-table th, .heatmap-table td {
  border: 1px solid #f0f0f0;
  padding: 6px 8px;
  text-align: center;
}

.run-col, .run-name-cell {
  text-align: left !important;
  white-space: nowrap;
  min-width: 130px;
  font-weight: 600;
  background: #fafafa;
}

.hour-col {
  font-size: 0.72rem;
  color: #999;
  background: #fafafa;
  min-width: 32px;
}

.heat-cell {
  cursor: default;
}

.cell-val {
  font-weight: 700;
  font-size: 0.72rem;
}

.legend {
  display: flex;
  gap: 16px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.78rem;
  color: #555;
}

.legend-swatch {
  width: 14px;
  height: 14px;
  border-radius: 2px;
  border: 1px solid #ddd;
}
</style>
