<template>
  <div class="ski-dashboard">
    <!-- Nav Bar -->
    <nav class="dash-nav">
      <div class="nav-brand">
        <router-link to="/" class="back-link">← MIROFISH</router-link>
        <span class="nav-divider">|</span>
        <span class="nav-ski">⛷ Avoriaz Ski Dashboard</span>
      </div>
      <div class="nav-right">
        <span class="refresh-indicator" :class="{ refreshing }">
          {{ refreshing ? '↺ Refreshing…' : `Updated ${lastRefresh}` }}
        </span>
        <button class="btn-refresh" :disabled="refreshing" @click="forceRefresh">
          ↺ Refresh Now
        </button>
      </div>
    </nav>

    <!-- Main grid -->
    <div class="dash-content">
      <!-- Row 1: Conditions + Cameras -->
      <div class="row row-top">
        <div class="col col-conditions">
          <ConditionsPanel ref="conditionsRef" />
        </div>
        <div class="col col-cameras">
          <CameraViewer ref="cameraRef" />
        </div>
      </div>

      <!-- Row 2: Recommendations (full width) -->
      <div class="row">
        <RecommendationsPanel ref="recsRef" @go-now="handleGoNow" />
      </div>

      <!-- Row 3: Day Plan -->
      <div class="row">
        <DayPlanPanel ref="dayPlanRef" />
      </div>

      <!-- Row 4: Charts grid -->
      <div class="row row-charts">
        <div class="col col-forecast">
          <ForecastChart ref="forecastRef" />
        </div>
        <div class="col col-heatmap">
          <CrowdHeatmap ref="heatmapRef" />
        </div>
      </div>

      <!-- Row 5: Stress tests -->
      <div class="row">
        <StressTests ref="stressRef" />
      </div>
    </div>

    <!-- "Go Now" modal -->
    <div v-if="goNowRun" class="go-modal-overlay" @click.self="goNowRun = null">
      <div class="go-modal">
        <div class="go-modal-header">
          <span>🎿 Head to {{ goNowRun.name }}!</span>
          <button class="modal-close" @click="goNowRun = null">✕</button>
        </div>
        <div class="go-modal-body">
          <p>
            <strong>Surface:</strong> {{ goNowRun.snow_surface }}<br>
            <strong>Temperature:</strong> {{ goNowRun.temperature_c }}°C<br>
            <strong>Crowd:</strong> {{ goNowRun.crowd_label }}<br>
            <strong>Primary lift:</strong> {{ goNowRun.primary_lift }}<br>
            <strong>Length:</strong> {{ goNowRun.length_km }} km<br>
          </p>
          <p class="go-reason" v-if="goNowRun.recommendation_reason">
            💡 {{ goNowRun.recommendation_reason }}
          </p>
          <div class="go-score-bar">
            <div class="go-score-fill" :style="{ width: goNowRun.enjoyment_score + '%' }"></div>
          </div>
          <div class="go-score-label">Enjoyment score: {{ goNowRun.enjoyment_score.toFixed(0) }}/100</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import ConditionsPanel from './ConditionsPanel.vue'
import RecommendationsPanel from './RecommendationsPanel.vue'
import CameraViewer from './CameraViewer.vue'
import DayPlanPanel from './DayPlanPanel.vue'
import ForecastChart from './Charts/ForecastChart.vue'
import CrowdHeatmap from './Charts/CrowdHeatmap.vue'
import StressTests from './Charts/StressTests.vue'
import { postRefresh } from '../../api/ski.js'

const conditionsRef = ref(null)
const cameraRef     = ref(null)
const recsRef       = ref(null)
const dayPlanRef    = ref(null)
const forecastRef   = ref(null)
const heatmapRef    = ref(null)
const stressRef     = ref(null)

const refreshing  = ref(false)
const lastRefresh = ref('—')
const goNowRun    = ref(null)

const REFRESH_MS = 10 * 60 * 1000

function updateRefreshTime() {
  lastRefresh.value = new Date().toLocaleTimeString()
}

async function forceRefresh() {
  if (refreshing.value) return
  refreshing.value = true
  try {
    await postRefresh()
    await Promise.all([
      conditionsRef.value?.refresh(),
      cameraRef.value?.refresh(),
      recsRef.value?.refresh(),
      dayPlanRef.value?.refresh(),
      forecastRef.value?.refresh(),
      heatmapRef.value?.refresh(),
      stressRef.value?.refresh(),
    ])
    updateRefreshTime()
  } catch (e) {
    console.error('Refresh error:', e)
  } finally {
    refreshing.value = false
  }
}

function handleGoNow(run) {
  goNowRun.value = run
}

let timer = null
onMounted(() => {
  updateRefreshTime()
  timer = setInterval(() => {
    forceRefresh()
  }, REFRESH_MS)
})
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.ski-dashboard {
  min-height: 100vh;
  background: #f7f8fa;
  font-family: 'JetBrains Mono', 'Space Grotesk', system-ui, monospace;
}

/* Nav */
.dash-nav {
  background: #000;
  color: #fff;
  height: 56px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 32px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-brand { display: flex; align-items: center; gap: 12px; }

.back-link {
  color: #fff;
  text-decoration: none;
  font-size: 0.85rem;
  opacity: 0.7;
  transition: opacity 0.2s;
}
.back-link:hover { opacity: 1; }

.nav-divider { color: #444; }

.nav-ski { font-size: 0.9rem; font-weight: 700; letter-spacing: 0.5px; }

.nav-right { display: flex; align-items: center; gap: 14px; }

.refresh-indicator {
  font-size: 0.75rem;
  color: #aaa;
}
.refresh-indicator.refreshing { color: #63b3ed; }

.btn-refresh {
  background: transparent;
  border: 1px solid #444;
  color: #fff;
  padding: 6px 14px;
  font-size: 0.78rem;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
}
.btn-refresh:hover:not(:disabled) { border-color: #fff; }
.btn-refresh:disabled { opacity: 0.4; cursor: not-allowed; }

/* Content grid */
.dash-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px 24px 48px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.row { width: 100%; }

.row-top, .row-charts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

@media (max-width: 900px) {
  .row-top, .row-charts { grid-template-columns: 1fr; }
}

/* Go-Now modal */
.go-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 500;
}

.go-modal {
  background: #fff;
  max-width: 420px;
  width: 90%;
  padding: 0;
  box-shadow: 0 4px 24px rgba(0,0,0,0.2);
}

.go-modal-header {
  background: #000;
  color: #fff;
  padding: 14px 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 700;
  font-size: 1rem;
}

.modal-close {
  background: transparent;
  border: none;
  color: #fff;
  font-size: 1.1rem;
  cursor: pointer;
  opacity: 0.7;
}
.modal-close:hover { opacity: 1; }

.go-modal-body { padding: 18px; font-size: 0.9rem; line-height: 1.8; }

.go-reason {
  font-style: italic;
  color: #555;
  border-left: 3px solid #ff4500;
  padding-left: 10px;
  margin: 10px 0;
}

.go-score-bar {
  height: 8px;
  background: #eee;
  border-radius: 4px;
  overflow: hidden;
  margin-top: 14px;
}

.go-score-fill {
  height: 100%;
  background: #ff4500;
  transition: width 0.4s;
}

.go-score-label {
  font-size: 0.78rem;
  color: #999;
  margin-top: 5px;
}
</style>
