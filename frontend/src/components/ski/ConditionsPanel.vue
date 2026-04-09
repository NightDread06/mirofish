<template>
  <div class="conditions-panel">
    <div class="panel-header">
      <span class="panel-title">⛷ Current Conditions</span>
      <span class="timestamp" v-if="data">{{ formattedTime }}</span>
    </div>

    <div v-if="loading" class="loading">Loading conditions…</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <template v-else-if="data">
      <!-- Primary metrics row -->
      <div class="metrics-grid">
        <div class="metric-card temp">
          <div class="metric-icon">🌡️</div>
          <div class="metric-value">{{ data.temperature_c }}°C</div>
          <div class="metric-label">Temperature</div>
        </div>
        <div class="metric-card snow">
          <div class="metric-icon">❄️</div>
          <div class="metric-value">{{ data.snowfall_24h_cm }} cm</div>
          <div class="metric-label">New Snow (24h)</div>
        </div>
        <div class="metric-card wind">
          <div class="metric-icon">💨</div>
          <div class="metric-value">{{ data.wind_kmh }} km/h</div>
          <div class="metric-label">Wind</div>
        </div>
        <div class="metric-card vis">
          <div class="metric-icon">👁️</div>
          <div class="metric-value capitalize">{{ data.visibility }}</div>
          <div class="metric-label">Visibility</div>
        </div>
      </div>

      <!-- Snow quality badge -->
      <div class="quality-row">
        <span class="quality-label">Snow quality:</span>
        <span class="quality-badge" :class="qualityClass">{{ data.snow_quality }}</span>
      </div>

      <!-- Cloud cover bar -->
      <div class="cloud-row">
        <span class="cloud-label">Cloud cover</span>
        <div class="cloud-bar-wrap">
          <div class="cloud-bar" :style="{ width: cloudPct + '%' }"></div>
        </div>
        <span class="cloud-pct">{{ cloudPct }}%</span>
      </div>

      <!-- Resort info -->
      <div class="resort-info">
        📍 {{ data.resort }} · {{ data.altitude_m }}m base
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getConditions } from '../../api/ski.js'

const data = ref(null)
const loading = ref(true)
const error = ref(null)

const REFRESH_MS = 10 * 60 * 1000  // 10 minutes

const formattedTime = computed(() => {
  if (!data.value?.timestamp) return ''
  return new Date(data.value.timestamp).toLocaleTimeString()
})

const cloudPct = computed(() => {
  if (!data.value) return 0
  return Math.round((data.value.cloud_cover ?? 0) * 100)
})

const qualityClass = computed(() => {
  const q = data.value?.snow_quality ?? ''
  if (q.includes('powder')) return 'quality-powder'
  if (q.includes('recent') || q.includes('packed')) return 'quality-good'
  if (q.includes('spring') || q.includes('groomed')) return 'quality-ok'
  return 'quality-default'
})

async function load() {
  loading.value = true
  error.value = null
  try {
    data.value = await getConditions()
  } catch (e) {
    error.value = 'Could not load conditions. Check backend connection.'
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

// Expose refresh so parent can trigger it
defineExpose({ refresh: load })
</script>

<style scoped>
.conditions-panel {
  background: #fff;
  border: 1px solid #e5e5e5;
  padding: 20px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.panel-title {
  font-weight: 700;
  font-size: 1rem;
  letter-spacing: 0.5px;
}

.timestamp {
  font-size: 0.75rem;
  color: #999;
  font-family: monospace;
}

.loading, .error {
  padding: 20px 0;
  color: #999;
  font-size: 0.9rem;
}

.error { color: #e53e3e; }

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

@media (max-width: 768px) {
  .metrics-grid { grid-template-columns: repeat(2, 1fr); }
}

.metric-card {
  border: 1px solid #f0f0f0;
  padding: 12px;
  text-align: center;
  background: #fafafa;
}

.metric-icon { font-size: 1.4rem; margin-bottom: 4px; }
.metric-value { font-size: 1.2rem; font-weight: 700; }
.metric-label { font-size: 0.72rem; color: #999; margin-top: 2px; }

.quality-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.quality-label { font-size: 0.85rem; color: #666; }

.quality-badge {
  padding: 3px 10px;
  border-radius: 3px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: capitalize;
}

.quality-powder  { background: #ebf8ff; color: #2b6cb0; }
.quality-good    { background: #f0fff4; color: #276749; }
.quality-ok      { background: #fffbeb; color: #975a16; }
.quality-default { background: #f7f7f7; color: #555; }

.cloud-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
  font-size: 0.82rem;
  color: #666;
}

.cloud-bar-wrap {
  flex: 1;
  height: 6px;
  background: #eee;
  border-radius: 3px;
  overflow: hidden;
}

.cloud-bar {
  height: 100%;
  background: #a0aec0;
  transition: width 0.4s;
}

.cloud-pct { width: 36px; text-align: right; color: #999; }

.resort-info {
  font-size: 0.78rem;
  color: #aaa;
  border-top: 1px solid #f0f0f0;
  padding-top: 10px;
}

.capitalize { text-transform: capitalize; }
</style>
