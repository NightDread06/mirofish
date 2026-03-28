<template>
  <div class="day-plan-panel">
    <div class="panel-header">
      <span class="panel-title">🗓 Hour-by-Hour Day Plan</span>
      <span class="plan-meta" v-if="plan">
        {{ plan.total_runs }} runs · {{ plan.total_km }} km total
      </span>
    </div>

    <div v-if="loading" class="loading">Generating day plan…</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <template v-else-if="plan && plan.slots.length">
      <div class="highlights" v-if="plan.highlights">
        💡 {{ plan.highlights }}
      </div>

      <div class="timeline">
        <div
          v-for="(slot, idx) in plan.slots"
          :key="idx"
          class="timeline-item"
          :class="'action-' + slotClass(slot.action)"
        >
          <div class="time-col">
            <div class="time-start">{{ slot.start_time }}</div>
            <div class="time-end">→ {{ slot.end_time }}</div>
          </div>
          <div class="time-connector">
            <div class="connector-dot" :class="'dot-' + slotClass(slot.action)"></div>
            <div class="connector-line" v-if="idx < plan.slots.length - 1"></div>
          </div>
          <div class="slot-body">
            <div class="slot-action">{{ slot.action }}</div>
            <div class="slot-run" v-if="slot.action === 'SKI'">{{ slot.run_name }}</div>
            <div class="slot-surface" v-if="slot.action === 'SKI'">
              {{ slot.snow_surface }} · {{ slot.crowd_label }} crowds ·
              ⭐ {{ slot.enjoyment_score?.toFixed(0) }}
            </div>
            <div class="slot-tip" v-if="slot.tip">{{ slot.tip }}</div>
          </div>
        </div>
      </div>
    </template>

    <div v-else class="empty">No day plan available.</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getDayPlan } from '../../api/ski.js'

const plan = ref(null)
const loading = ref(true)
const error = ref(null)

const REFRESH_MS = 10 * 60 * 1000

function slotClass(action) {
  if (!action) return 'default'
  if (action === 'SKI') return 'ski'
  if (action.includes('LUNCH')) return 'lunch'
  return 'default'
}

async function load() {
  loading.value = true
  error.value = null
  try {
    plan.value = await getDayPlan()
  } catch (e) {
    error.value = 'Could not load day plan.'
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
.day-plan-panel {
  background: #fff;
  border: 1px solid #e5e5e5;
  padding: 20px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.panel-title { font-weight: 700; font-size: 1rem; }
.plan-meta   { font-size: 0.78rem; color: #999; }

.loading, .error, .empty {
  padding: 20px 0;
  font-size: 0.9rem;
  color: #999;
}
.error { color: #e53e3e; }

.highlights {
  font-size: 0.85rem;
  color: #555;
  font-style: italic;
  border-left: 3px solid #ff4500;
  padding-left: 10px;
  margin-bottom: 16px;
}

.timeline { display: flex; flex-direction: column; }

.timeline-item {
  display: flex;
  gap: 0;
  position: relative;
}

.time-col {
  min-width: 80px;
  text-align: right;
  padding-right: 12px;
  padding-top: 4px;
  flex-shrink: 0;
}

.time-start { font-size: 0.82rem; font-weight: 700; color: #333; }
.time-end   { font-size: 0.72rem; color: #aaa; }

.time-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  width: 20px;
}

.connector-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-top: 6px;
  flex-shrink: 0;
}
.dot-ski   { background: #3182ce; }
.dot-lunch { background: #f6ad55; }
.dot-default { background: #ccc; }

.connector-line {
  flex: 1;
  width: 2px;
  background: #e2e8f0;
  min-height: 20px;
}

.slot-body {
  padding: 4px 0 16px 12px;
  flex: 1;
}

.slot-action {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 1px;
  color: #999;
  text-transform: uppercase;
  margin-bottom: 2px;
}

.action-ski .slot-action   { color: #3182ce; }
.action-lunch .slot-action { color: #dd6b20; }

.slot-run {
  font-weight: 700;
  font-size: 0.95rem;
  margin-bottom: 2px;
}

.slot-surface {
  font-size: 0.78rem;
  color: #888;
  margin-bottom: 4px;
}

.slot-tip {
  font-size: 0.8rem;
  color: #555;
  font-style: italic;
}
</style>
