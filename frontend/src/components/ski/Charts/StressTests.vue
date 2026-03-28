<template>
  <div class="stress-tests">
    <div class="chart-title">⚠️ Stress Test Scenarios</div>

    <div v-if="loading" class="loading">Running scenarios…</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <template v-else-if="scenarios.length">
      <div class="scenario-list">
        <div v-for="s in scenarios" :key="s.name" class="scenario-card">
          <div class="scenario-header">
            <span class="scenario-name">{{ s.name }}</span>
            <span class="delta-badge" :class="deltaClass(s.delta_enjoyment)">
              {{ s.delta_enjoyment > 0 ? '+' : '' }}{{ s.delta_enjoyment }} pts
            </span>
          </div>
          <div class="scenario-desc">{{ s.description }}</div>
          <div class="scenario-impact">{{ s.key_impact }}</div>

          <div class="scenario-runs">
            <div v-for="run in s.runs" :key="run.name" class="scenario-run">
              <span class="run-name">{{ run.name }}</span>
              <span class="run-score">⭐ {{ run.enjoyment_score.toFixed(0) }}</span>
              <span class="run-surface">{{ run.snow_surface }}</span>
            </div>
          </div>
        </div>
      </div>
    </template>

    <div v-else class="empty">No stress test data.</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getStressTests } from '../../../api/ski.js'

const scenarios = ref([])
const loading = ref(true)
const error = ref(null)

function deltaClass(delta) {
  if (delta > 5) return 'delta-pos'
  if (delta < -5) return 'delta-neg'
  return 'delta-neutral'
}

async function load() {
  loading.value = true
  error.value = null
  try {
    const data = await getStressTests()
    scenarios.value = data.scenarios || []
  } catch (e) {
    error.value = 'Could not load stress tests.'
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
.stress-tests {
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

.scenario-list { display: flex; flex-direction: column; gap: 14px; }

.scenario-card {
  border: 1px solid #f0f0f0;
  padding: 14px;
  background: #fafafa;
}

.scenario-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.scenario-name { font-weight: 700; font-size: 0.95rem; }

.delta-badge {
  font-size: 0.78rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 10px;
}
.delta-pos     { background: #c6f6d5; color: #22543d; }
.delta-neg     { background: #fed7d7; color: #742a2a; }
.delta-neutral { background: #e2e8f0; color: #4a5568; }

.scenario-desc {
  font-size: 0.82rem;
  color: #666;
  margin-bottom: 4px;
}

.scenario-impact {
  font-size: 0.8rem;
  color: #555;
  font-style: italic;
  margin-bottom: 10px;
  border-left: 2px solid #e2e8f0;
  padding-left: 8px;
}

.scenario-runs { display: flex; flex-direction: column; gap: 5px; }

.scenario-run {
  display: flex;
  gap: 10px;
  align-items: center;
  font-size: 0.8rem;
  padding: 4px 0;
  border-top: 1px solid #f0f0f0;
}

.run-name { flex: 1; font-weight: 600; }
.run-score { color: #744210; font-weight: 600; }
.run-surface { color: #999; font-size: 0.75rem; }
</style>
