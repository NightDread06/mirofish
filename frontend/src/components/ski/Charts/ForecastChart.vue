<template>
  <div class="forecast-chart">
    <div class="chart-title">📅 8-Day Forecast</div>

    <div v-if="loading" class="loading">Loading forecast…</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <template v-else-if="days.length">
      <div class="day-grid">
        <div v-for="day in days" :key="day.date" class="day-card">
          <div class="day-label">{{ formatDay(day.date) }}</div>
          <div class="day-icon">{{ weatherIcon(day) }}</div>
          <div class="day-temps">
            <span class="temp-high">{{ fmt(day.temp_max_c) }}°</span>
            <span class="temp-sep">/</span>
            <span class="temp-low">{{ fmt(day.temp_min_c) }}°</span>
          </div>
          <div class="day-snow" v-if="day.snowfall_cm > 0">
            ❄️ {{ fmt(day.snowfall_cm) }} cm
          </div>
          <div class="day-wind">
            💨 {{ fmt(day.wind_max_kmh) }} km/h
          </div>
        </div>
      </div>
    </template>

    <div v-else class="empty">No forecast data.</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getForecast } from '../../../api/ski.js'

const days = ref([])
const loading = ref(true)
const error = ref(null)

const REFRESH_MS = 10 * 60 * 1000

function fmt(v) {
  return v != null ? Number(v).toFixed(1) : '–'
}

function formatDay(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr + 'T12:00:00')
  return d.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })
}

function weatherIcon(day) {
  if ((day.snowfall_cm ?? 0) > 5) return '🌨️'
  if ((day.snowfall_cm ?? 0) > 0) return '🌦️'
  if ((day.temp_max_c ?? 0) > 3)  return '☀️'
  return '⛅'
}

async function load() {
  loading.value = true
  error.value = null
  try {
    const data = await getForecast()
    days.value = data.days || []
  } catch (e) {
    error.value = 'Could not load forecast.'
  } finally {
    loading.value = false
  }
}

let timer = null
onMounted(() => {
  load()
  timer = setInterval(load, REFRESH_MS)
})
onUnmounted(() => clearInterval(timer))

defineExpose({ refresh: load })
</script>

<style scoped>
.forecast-chart {
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

.day-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 8px;
}

@media (max-width: 900px) {
  .day-grid { grid-template-columns: repeat(4, 1fr); }
}

@media (max-width: 500px) {
  .day-grid { grid-template-columns: repeat(2, 1fr); }
}

.day-card {
  border: 1px solid #f0f0f0;
  padding: 10px 8px;
  text-align: center;
  background: #fafafa;
}

.day-label {
  font-size: 0.72rem;
  color: #999;
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.day-icon { font-size: 1.4rem; margin-bottom: 6px; }

.day-temps {
  font-size: 0.85rem;
  margin-bottom: 4px;
}

.temp-high { font-weight: 700; color: #e53e3e; }
.temp-sep  { color: #ccc; margin: 0 2px; }
.temp-low  { color: #3182ce; }

.day-snow, .day-wind {
  font-size: 0.72rem;
  color: #888;
  margin-top: 3px;
}
</style>
