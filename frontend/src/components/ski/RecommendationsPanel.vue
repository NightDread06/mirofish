<template>
  <div class="recommendations-panel">
    <div class="panel-header">
      <span class="panel-title">🏆 Top 3 Runs Right Now</span>
      <div class="prefs-row">
        <label>
          Snow
          <input type="range" min="0" max="1" step="0.1" v-model.number="prefs.prioritize_snow" @change="load" />
          {{ pct(prefs.prioritize_snow) }}
        </label>
        <label>
          Anti-crowd
          <input type="range" min="0" max="1" step="0.1" v-model.number="prefs.avoid_crowds" @change="load" />
          {{ pct(prefs.avoid_crowds) }}
        </label>
        <select v-model="prefs.difficulty_level" @change="load">
          <option value="all">All levels</option>
          <option value="beginner">Beginner</option>
          <option value="intermediate">Intermediate</option>
          <option value="advanced">Advanced</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading recommendations…</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <div v-else-if="runs.length" class="runs-list">
      <div v-for="(run, idx) in runs" :key="run.name" class="run-card">
        <div class="run-rank">#{{ idx + 1 }}</div>
        <div class="run-body">
          <div class="run-top">
            <span class="run-name">{{ run.name }}</span>
            <span class="run-diff" :class="'diff-' + run.difficulty">{{ run.difficulty }}</span>
          </div>
          <div class="run-scores">
            <div class="score-pill enjoyment">
              ⭐ {{ run.enjoyment_score.toFixed(0) }}/100
            </div>
            <div class="score-pill snow">
              ❄️ Snow {{ run.snow_score.toFixed(0) }}
            </div>
            <div class="score-pill crowd" :class="'crowd-' + run.crowd_label.toLowerCase()">
              👥 {{ run.crowd_label }}
            </div>
          </div>
          <div class="run-surface">{{ run.snow_surface }} · {{ run.temperature_c }}°C · {{ run.length_km }} km</div>
          <div class="run-reason" v-if="run.recommendation_reason">
            💡 {{ run.recommendation_reason }}
          </div>
          <div class="run-actions">
            <button class="btn-go" @click="emit('go-now', run)">Go Now</button>
            <button class="btn-detail" @click="toggleDetail(idx)">
              {{ expandedIdx === idx ? 'Less' : 'Details' }}
            </button>
          </div>

          <!-- Expanded detail -->
          <div v-if="expandedIdx === idx" class="run-detail">
            <div class="detail-row">
              <span>Altitude</span><span>{{ run.altitude_m }}m</span>
            </div>
            <div class="detail-row">
              <span>Orientation</span><span>{{ run.orientation }}</span>
            </div>
            <div class="detail-row">
              <span>Primary lift</span><span>{{ run.primary_lift }}</span>
            </div>
            <div class="detail-row">
              <span>Flow score</span><span>{{ (run.flow_score * 100).toFixed(0) }}/100</span>
            </div>
            <!-- Enjoyment breakdown bar -->
            <div class="score-breakdown">
              <div class="breakdown-label">Score breakdown</div>
              <div class="breakdown-bar">
                <div class="seg snow-seg"   :style="{ width: snowPct(run) + '%' }" title="Snow (35%)"></div>
                <div class="seg crowd-seg"  :style="{ width: crowdPct(run) + '%' }" title="Crowd (30%)"></div>
                <div class="seg length-seg" :style="{ width: lenPct(run) + '%' }" title="Length (15%)"></div>
                <div class="seg flow-seg"   :style="{ width: flowPct(run) + '%' }" title="Flow (20%)"></div>
              </div>
              <div class="breakdown-legend">
                <span class="legend-item snow-seg">Snow 35%</span>
                <span class="legend-item crowd-seg">Crowd 30%</span>
                <span class="legend-item length-seg">Length 15%</span>
                <span class="legend-item flow-seg">Flow 20%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="empty">No runs available for selected filters.</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getRecommendations } from '../../api/ski.js'

const emit = defineEmits(['go-now'])

const runs = ref([])
const loading = ref(true)
const error = ref(null)
const expandedIdx = ref(null)

const prefs = ref({
  prioritize_snow: 0.5,
  avoid_crowds: 0.5,
  difficulty_level: 'all',
})

const pct = v => Math.round(v * 100) + '%'

const REFRESH_MS = 10 * 60 * 1000

function toggleDetail(idx) {
  expandedIdx.value = expandedIdx.value === idx ? null : idx
}

// Enjoyment breakdown proportions (scaled to 100%)
function snowPct(run)  { return (run.snow_score  * 0.35).toFixed(0) }
function crowdPct(run) { return ((1 - run.crowd_level) * 100 * 0.30).toFixed(0) }
function lenPct(run)   { return Math.min(100, run.length_km / 5 * 100 * 0.15).toFixed(0) }
function flowPct(run)  { return (run.flow_score * 100 * 0.20).toFixed(0) }

async function load() {
  loading.value = true
  error.value = null
  try {
    const data = await getRecommendations(prefs.value)
    runs.value = data.runs || []
  } catch (e) {
    error.value = 'Could not load recommendations.'
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
.recommendations-panel {
  background: #fff;
  border: 1px solid #e5e5e5;
  padding: 20px;
}

.panel-header {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}

.panel-title { font-weight: 700; font-size: 1rem; }

.prefs-row {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  align-items: center;
  font-size: 0.78rem;
  color: #666;
}

.prefs-row label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.prefs-row input[type="range"] { width: 80px; }

.prefs-row select {
  border: 1px solid #ddd;
  padding: 3px 6px;
  font-size: 0.78rem;
  background: #fafafa;
}

.loading, .error, .empty {
  padding: 20px 0;
  color: #999;
  font-size: 0.9rem;
}
.error { color: #e53e3e; }

.runs-list { display: flex; flex-direction: column; gap: 14px; }

.run-card {
  display: flex;
  gap: 12px;
  border: 1px solid #f0f0f0;
  padding: 14px;
  background: #fafafa;
}

.run-rank {
  font-size: 1.6rem;
  font-weight: 800;
  color: #e2e8f0;
  min-width: 36px;
  display: flex;
  align-items: flex-start;
  padding-top: 2px;
}

.run-body { flex: 1; }

.run-top {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.run-name { font-weight: 700; font-size: 1.02rem; }

.run-diff {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 3px;
  text-transform: uppercase;
}
.diff-green  { background: #c6f6d5; color: #22543d; }
.diff-blue   { background: #bee3f8; color: #2a4365; }
.diff-red    { background: #fed7d7; color: #742a2a; }
.diff-black  { background: #1a202c; color: #fff; }

.run-scores {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 7px;
}

.score-pill {
  font-size: 0.78rem;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
}
.score-pill.enjoyment { background: #fefcbf; color: #744210; }
.score-pill.snow      { background: #ebf8ff; color: #2c5282; }
.score-pill.crowd     { background: #f7f7f7; color: #555; }
.crowd-low    { background: #c6f6d5 !important; color: #22543d !important; }
.crowd-medium { background: #fefcbf !important; color: #744210 !important; }
.crowd-high   { background: #fed7d7 !important; color: #742a2a !important; }

.run-surface  { font-size: 0.8rem; color: #888; margin-bottom: 6px; }
.run-reason   { font-size: 0.8rem; color: #555; font-style: italic; margin-bottom: 8px; }

.run-actions  { display: flex; gap: 8px; }

.btn-go {
  background: #000;
  color: #fff;
  border: none;
  padding: 6px 16px;
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-go:hover { background: #ff4500; }

.btn-detail {
  background: transparent;
  color: #555;
  border: 1px solid #ddd;
  padding: 6px 14px;
  font-size: 0.82rem;
  cursor: pointer;
  transition: border-color 0.2s;
}
.btn-detail:hover { border-color: #999; }

/* Expanded detail */
.run-detail {
  margin-top: 12px;
  border-top: 1px solid #eee;
  padding-top: 10px;
  font-size: 0.82rem;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 3px 0;
  color: #666;
}
.detail-row span:last-child { font-weight: 600; color: #333; }

.score-breakdown { margin-top: 10px; }
.breakdown-label { font-size: 0.75rem; color: #999; margin-bottom: 5px; }

.breakdown-bar {
  display: flex;
  height: 10px;
  border-radius: 4px;
  overflow: hidden;
  gap: 1px;
}

.seg { height: 100%; }
.snow-seg   { background: #63b3ed; }
.crowd-seg  { background: #68d391; }
.length-seg { background: #f6ad55; }
.flow-seg   { background: #b794f4; }

.breakdown-legend {
  display: flex;
  gap: 12px;
  margin-top: 6px;
  flex-wrap: wrap;
}

.legend-item {
  font-size: 0.7rem;
  padding: 1px 6px;
  border-radius: 3px;
  opacity: 0.85;
}
</style>
