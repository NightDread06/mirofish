<template>
  <div class="ski-app">
    <!-- NAV -->
    <nav class="navbar">
      <router-link to="/" class="nav-brand">MIROFISH</router-link>
      <div class="nav-center">
        <span class="nav-badge">⛷ AVORIAZ SKI ASSISTANT</span>
        <span class="nav-season">Season ends 04 Apr 2026</span>
      </div>
      <div class="nav-right">
        <span class="engine-tag">Powered by Mirofish Decision Engine v1.0</span>
      </div>
    </nav>

    <!-- CONTROLS -->
    <div class="controls-bar">
      <div class="controls-inner">
        <div class="ctrl-group">
          <label class="ctrl-label">QUERY TIME</label>
          <input
            type="datetime-local"
            v-model="params.time"
            class="ctrl-input"
            min="2026-03-28T08:00"
            max="2026-04-04T17:00"
          />
        </div>
        <div class="ctrl-group">
          <label class="ctrl-label">DIFFICULTY</label>
          <select v-model="params.difficulty" class="ctrl-select">
            <option value="all">All</option>
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
        </div>
        <div class="ctrl-group">
          <label class="ctrl-label">SNOW PRIORITY <span class="ctrl-val">{{ Math.round(params.prioritizeSnow * 100) }}%</span></label>
          <input type="range" v-model.number="params.prioritizeSnow" min="0" max="1" step="0.05" class="ctrl-slider" />
        </div>
        <div class="ctrl-group">
          <label class="ctrl-label">CROWD AVOIDANCE <span class="ctrl-val">{{ Math.round(params.avoidCrowds * 100) }}%</span></label>
          <input type="range" v-model.number="params.avoidCrowds" min="0" max="1" step="0.05" class="ctrl-slider" />
        </div>
        <div class="ctrl-group">
          <label class="ctrl-label">TOURIST INFLUX <span class="ctrl-val">×{{ params.tourists.toFixed(1) }}</span></label>
          <input type="range" v-model.number="params.tourists" min="0.5" max="2.0" step="0.1" class="ctrl-slider" />
        </div>
        <button class="run-btn" @click="runAll" :disabled="loading">
          <span v-if="!loading">RUN ANALYSIS →</span>
          <span v-else class="loading-dots">COMPUTING<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span></span>
        </button>
      </div>
    </div>

    <!-- ERROR -->
    <div v-if="error" class="error-banner">
      {{ error }}
    </div>

    <!-- CONTENT -->
    <div v-if="data.dashboard" class="content">

      <!-- ── SECTION 1: LIVE DASHBOARD ── -->
      <section class="section">
        <div class="section-header">
          <span class="section-icon">🟢</span>
          <span class="section-title">LIVE RECOMMENDATIONS — WHERE TO SKI RIGHT NOW</span>
          <span class="section-meta">{{ formatTimestamp(data.dashboard.timestamp) }}</span>
        </div>
        <div class="top3-grid">
          <div
            v-for="(rc, i) in data.dashboard.top_3"
            :key="rc.run.name"
            class="run-card"
            :class="`rank-${i + 1}`"
          >
            <div class="card-rank">#{{ i + 1 }}</div>
            <div class="card-name">{{ rc.run.name }}</div>
            <div class="card-badges">
              <span class="badge" :class="`diff-${rc.run.difficulty}`">{{ rc.run.difficulty.toUpperCase() }}</span>
              <span class="badge orient">{{ rc.run.orientation }}</span>
              <span class="badge alt">{{ rc.run.altitude_m }}m</span>
            </div>
            <div class="card-score-row">
              <div class="score-block">
                <div class="score-val">{{ rc.enjoyment_score.toFixed(0) }}</div>
                <div class="score-lbl">Enjoyment</div>
              </div>
              <div class="score-block">
                <div class="score-val">{{ rc.snow_score.toFixed(0) }}</div>
                <div class="score-lbl">Snow</div>
              </div>
              <div class="score-block">
                <div class="score-val" :class="`crowd-${rc.crowd_label.toLowerCase()}`">{{ rc.crowd_label }}</div>
                <div class="score-lbl">Crowds</div>
              </div>
            </div>
            <div class="card-surface">{{ rc.snow_surface }} · {{ rc.temperature_c }}°C</div>
            <div class="card-reason">{{ rc.recommendation_reason }}</div>
            <div class="card-meta">{{ rc.run.length_km }}km · {{ rc.run.primary_lift }}</div>
          </div>
        </div>
      </section>

      <!-- ── SECTION 2: TIME STRATEGY ── -->
      <section class="section">
        <div class="section-header">
          <span class="section-icon">📅</span>
          <span class="section-title">TIME-AWARE STRATEGY — FULL DAY BREAKDOWN</span>
        </div>
        <div class="strategy-grid" v-if="data.strategy">
          <div v-for="s in data.strategy.strategies" :key="s.slot" class="strategy-col">
            <div class="strategy-slot">{{ s.slot }}</div>
            <div class="strategy-time">{{ s.time_range }}</div>
            <div class="strategy-rationale">{{ s.rationale }}</div>
            <div class="strategy-subsection">
              <div class="strategy-sub-label go">GO →</div>
              <div v-for="rc in s.top_runs" :key="rc.run.name" class="strategy-run go-run">
                <span class="sr-name">{{ rc.run.name }}</span>
                <span class="sr-score">{{ rc.enjoyment_score.toFixed(0) }}</span>
                <span class="badge" :class="`diff-${rc.run.difficulty}`">{{ rc.run.difficulty }}</span>
              </div>
            </div>
            <div class="strategy-subsection" v-if="s.avoid_runs.length">
              <div class="strategy-sub-label avoid">AVOID ✗</div>
              <div v-for="rc in s.avoid_runs" :key="rc.run.name" class="strategy-run avoid-run">
                <span class="sr-name">{{ rc.run.name }}</span>
                <span class="sr-surface">{{ rc.snow_surface }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ── SECTION 3: DAY ITINERARY ── -->
      <section class="section">
        <div class="section-header">
          <span class="section-icon">🎯</span>
          <span class="section-title">DAILY ITINERARY — HOUR-BY-HOUR PLAN</span>
          <span v-if="data.itinerary" class="section-meta">
            {{ data.itinerary.total_runs }} runs · {{ data.itinerary.total_km }} km
          </span>
        </div>
        <div v-if="data.itinerary" class="itinerary-wrap">
          <div class="itinerary-highlights">{{ data.itinerary.highlights }}</div>
          <div class="itinerary-timeline">
            <div
              v-for="slot in data.itinerary.slots"
              :key="slot.start_time"
              class="itinerary-slot"
              :class="slot.action === 'LUNCH BREAK' ? 'lunch' : 'ski'"
            >
              <div class="it-time">{{ formatTime(slot.start_time) }}</div>
              <div class="it-connector">
                <div class="it-dot" :class="slot.action === 'LUNCH BREAK' ? 'dot-lunch' : `diff-${slot.run_difficulty}`"></div>
                <div class="it-line"></div>
              </div>
              <div class="it-content">
                <div class="it-action">{{ slot.action }}</div>
                <div class="it-run">{{ slot.run_name }}</div>
                <div v-if="slot.action !== 'LUNCH BREAK'" class="it-meta">
                  <span class="badge" :class="`diff-${slot.run_difficulty}`">{{ slot.run_difficulty }}</span>
                  <span class="it-surface">{{ slot.snow_surface }}</span>
                  <span :class="`crowd-${slot.crowd_label.toLowerCase()}`">{{ slot.crowd_label }} crowds</span>
                  <span class="it-enj">{{ slot.enjoyment_score.toFixed(0) }}/100</span>
                </div>
                <div class="it-tip">{{ slot.tip }}</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ── SECTION 4: HIDDEN GEMS ── -->
      <section class="section" v-if="data.gems">
        <div class="section-header">
          <span class="section-icon">💎</span>
          <span class="section-title">HIDDEN GEMS — CONTRARIAN INTELLIGENCE</span>
        </div>
        <div v-if="data.gems.gems.length === 0" class="empty-state">
          No hidden gems found for current preferences — broaden difficulty to find them.
        </div>
        <div v-else class="gems-grid">
          <div v-for="g in data.gems.gems" :key="g.run.name" class="gem-card">
            <div class="gem-header">
              <span class="gem-name">{{ g.run.name }}</span>
              <span class="gem-alpha">α {{ g.alpha_score.toFixed(1) }}</span>
            </div>
            <div class="gem-badges">
              <span class="badge" :class="`diff-${g.run.difficulty}`">{{ g.run.difficulty }}</span>
              <span class="badge alt">{{ g.run.altitude_m }}m</span>
              <span class="badge orient">{{ g.run.orientation }}</span>
              <span class="badge enj">{{ g.conditions.enjoyment_score.toFixed(0) }}/100</span>
            </div>
            <div class="gem-why">
              <div class="gem-why-label">WHY HIDDEN</div>
              <div class="gem-why-text">{{ g.why_hidden }}</div>
            </div>
            <div class="gem-why">
              <div class="gem-why-label excellent">WHY EXCELLENT</div>
              <div class="gem-why-text">{{ g.why_excellent }}</div>
            </div>
          </div>
        </div>
      </section>

      <!-- ── SECTION 5: SENSITIVITY ── -->
      <section class="section" v-if="data.sensitivity">
        <div class="section-header">
          <span class="section-icon">📊</span>
          <span class="section-title">MODEL INSIGHTS — SENSITIVITY ANALYSIS</span>
        </div>
        <div class="sensitivity-table">
          <div class="sens-header sens-row">
            <span>Variable</span>
            <span>Base Avg</span>
            <span>Shocked</span>
            <span>Δ</span>
            <span>% Change</span>
          </div>
          <div
            v-for="r in data.sensitivity.sensitivity"
            :key="r.variable"
            class="sens-row"
          >
            <span class="sens-var">{{ r.variable }}</span>
            <span class="sens-num">{{ r.base_avg }}</span>
            <span class="sens-num">{{ r.shocked_avg }}</span>
            <span class="sens-delta" :class="r.delta < 0 ? 'neg' : 'pos'">
              {{ r.delta > 0 ? '+' : '' }}{{ r.delta }}
            </span>
            <span class="sens-pct" :class="r.pct_change < 0 ? 'neg' : 'pos'">
              {{ r.pct_change > 0 ? '+' : '' }}{{ r.pct_change }}%
            </span>
          </div>
        </div>
        <div class="sensitivity-interps">
          <div v-for="r in data.sensitivity.sensitivity" :key="r.variable + '-i'" class="interp-block">
            <div class="interp-var">{{ r.variable }}</div>
            <div class="interp-text">{{ r.interpretation }}</div>
          </div>
        </div>
      </section>

      <!-- ── SECTION 6: STRESS TESTS ── -->
      <section class="section" v-if="data.stress">
        <div class="section-header">
          <span class="section-icon">⚠</span>
          <span class="section-title">STRESS TESTS — HOW RECOMMENDATIONS SHIFT</span>
        </div>
        <div class="stress-grid">
          <div v-for="s in data.stress.scenarios" :key="s.name" class="stress-card">
            <div class="stress-name">{{ s.name }}</div>
            <div class="stress-desc">{{ s.description }}</div>
            <div class="stress-cols">
              <div class="stress-col">
                <div class="stress-col-label go">BEST RUNS</div>
                <div v-for="rc in s.top_3" :key="rc.run.name" class="stress-run">
                  <span class="badge" :class="`diff-${rc.run.difficulty}`">{{ rc.run.difficulty }}</span>
                  <span class="sr-name">{{ rc.run.name }}</span>
                  <span class="sr-score">{{ rc.enjoyment_score.toFixed(0) }}</span>
                </div>
              </div>
              <div class="stress-col">
                <div class="stress-col-label avoid">WORST RUNS</div>
                <div v-for="rc in s.worst_3" :key="rc.run.name" class="stress-run avoid">
                  <span class="badge" :class="`diff-${rc.run.difficulty}`">{{ rc.run.difficulty }}</span>
                  <span class="sr-name">{{ rc.run.name }}</span>
                  <span class="sr-score">{{ rc.enjoyment_score.toFixed(0) }}</span>
                </div>
              </div>
            </div>
            <div class="stress-insight">
              <span class="insight-label">KEY INSIGHT</span>
              {{ s.key_insight }}
            </div>
          </div>
        </div>
      </section>

      <!-- ── SECTION 7: DECISION RULES ── -->
      <section class="section" v-if="data.rules">
        <div class="section-header">
          <span class="section-icon">📋</span>
          <span class="section-title">STRATEGY — FIELD-READY DECISION RULES</span>
        </div>
        <div class="rules-list">
          <div v-for="(r, i) in data.rules.rules" :key="i" class="rule-card">
            <div class="rule-num">{{ String(i + 1).padStart(2, '0') }}</div>
            <div class="rule-body">
              <div class="rule-condition">IF: {{ r.condition }}</div>
              <div class="rule-action">THEN: {{ r.action }}</div>
              <div class="rule-rationale">{{ r.rationale }}</div>
            </div>
          </div>
        </div>
      </section>

    </div>

    <!-- EMPTY STATE -->
    <div v-else-if="!loading" class="splash">
      <div class="splash-icon">⛷</div>
      <div class="splash-title">Avoriaz Ski Assistant</div>
      <div class="splash-sub">Configure preferences above and click RUN ANALYSIS to get live recommendations.</div>
      <div class="splash-season">Season: 28 Mar – 04 Apr 2026 · Portes du Soleil</div>
    </div>

    <!-- LOADING -->
    <div v-if="loading" class="loading-overlay">
      <div class="loading-card">
        <div class="loading-ski">⛷</div>
        <div class="loading-text">Running simulation engine...</div>
        <div class="loading-bar"><div class="loading-fill"></div></div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { skiApi } from '../api/ski.js'

const loading = ref(false)
const error = ref('')

// Default to today at 10:00 (within season)
const params = reactive({
  time: '2026-03-28T10:00',
  difficulty: 'all',
  prioritizeSnow: 0.5,
  avoidCrowds: 0.5,
  tourists: 1.0,
})

const data = reactive({
  dashboard: null,
  strategy: null,
  itinerary: null,
  gems: null,
  sensitivity: null,
  stress: null,
  rules: null,
})

function buildOpts() {
  return {
    time: params.time.replace('T', ' '),
    difficulty: params.difficulty,
    prioritizeSnow: params.prioritizeSnow,
    avoidCrowds: params.avoidCrowds,
    tourists: params.tourists,
    seed: 42,
  }
}

async function runAll() {
  loading.value = true
  error.value = ''
  const opts = buildOpts()
  try {
    const [dashboard, strategy, itinerary, gems, sensitivity, stress, rules] = await Promise.all([
      skiApi.getDashboard(opts),
      skiApi.getStrategy(opts),
      skiApi.getItinerary(opts),
      skiApi.getGems(opts),
      skiApi.getSensitivity(opts),
      skiApi.getStress(opts),
      skiApi.getRules(opts),
    ])
    data.dashboard = dashboard
    data.strategy = strategy
    data.itinerary = itinerary
    data.gems = gems
    data.sensitivity = sensitivity
    data.stress = stress
    data.rules = rules
  } catch (e) {
    error.value = e?.response?.data?.error || e.message || 'Failed to load ski data.'
  } finally {
    loading.value = false
  }
}

function formatTimestamp(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleString('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function formatTime(iso) {
  if (!iso) return ''
  return iso.slice(11, 16)
}
</script>

<style scoped>
/* ── VARIABLES ── */
:root {
  --black: #000;
  --white: #fff;
  --orange: #FF4500;
  --border: #E5E5E5;
  --mono: 'JetBrains Mono', monospace;
  --sans: 'Space Grotesk', system-ui, sans-serif;
}

* { box-sizing: border-box; }

.ski-app {
  min-height: 100vh;
  background: #fff;
  font-family: 'Space Grotesk', system-ui, sans-serif;
  color: #000;
}

/* ── NAV ── */
.navbar {
  height: 56px;
  background: #000;
  color: #fff;
  display: flex;
  align-items: center;
  padding: 0 32px;
  gap: 24px;
  position: sticky;
  top: 0;
  z-index: 100;
}
.nav-brand {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  font-size: 1.1rem;
  color: #fff;
  text-decoration: none;
  letter-spacing: 1px;
  flex-shrink: 0;
}
.nav-center {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}
.nav-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.5px;
}
.nav-season {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #888;
}
.nav-right {
  flex-shrink: 0;
}
.engine-tag {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  color: #666;
}

/* ── CONTROLS ── */
.controls-bar {
  background: #f5f5f5;
  border-bottom: 1px solid #e5e5e5;
  padding: 16px 32px;
}
.controls-inner {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  align-items: flex-end;
  gap: 24px;
  flex-wrap: wrap;
}
.ctrl-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.ctrl-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  font-weight: 700;
  color: #666;
  letter-spacing: 1px;
  display: flex;
  justify-content: space-between;
  gap: 8px;
}
.ctrl-val {
  color: #FF4500;
  font-weight: 700;
}
.ctrl-input, .ctrl-select {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  border: 1px solid #ccc;
  padding: 6px 10px;
  background: #fff;
  outline: none;
  color: #000;
  height: 34px;
}
.ctrl-input:focus, .ctrl-select:focus {
  border-color: #000;
}
.ctrl-slider {
  -webkit-appearance: none;
  width: 160px;
  height: 3px;
  background: #ccc;
  outline: none;
  cursor: pointer;
}
.ctrl-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 14px;
  height: 14px;
  background: #000;
  cursor: pointer;
  border-radius: 0;
}
.run-btn {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  font-size: 0.85rem;
  background: #000;
  color: #fff;
  border: none;
  padding: 0 28px;
  height: 34px;
  cursor: pointer;
  letter-spacing: 1px;
  flex-shrink: 0;
  transition: background 0.2s;
}
.run-btn:hover:not(:disabled) { background: #FF4500; }
.run-btn:disabled { background: #ccc; cursor: not-allowed; }

.loading-dots .dot {
  animation: blink 1.2s infinite;
}
.loading-dots .dot:nth-child(2) { animation-delay: 0.4s; }
.loading-dots .dot:nth-child(3) { animation-delay: 0.8s; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }

/* ── ERROR ── */
.error-banner {
  background: #fff0ee;
  border-left: 3px solid #FF4500;
  padding: 12px 32px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  color: #c00;
}

/* ── CONTENT ── */
.content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 40px 32px;
  display: flex;
  flex-direction: column;
  gap: 56px;
}

.section {}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 2px solid #000;
}
.section-icon { font-size: 1.2rem; }
.section-title {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  font-size: 0.85rem;
  letter-spacing: 1px;
  color: #000;
  flex: 1;
}
.section-meta {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #888;
}

/* ── BADGES ── */
.badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 2px 7px;
  display: inline-block;
  letter-spacing: 0.5px;
}
.diff-green  { background: #22c55e; color: #fff; }
.diff-blue   { background: #3b82f6; color: #fff; }
.diff-red    { background: #ef4444; color: #fff; }
.diff-black  { background: #000; color: #fff; }
.orient { background: #e5e5e5; color: #333; }
.alt    { background: #e5e5e5; color: #333; }
.enj    { background: #FF4500; color: #fff; }

/* ── CROWD LABELS ── */
.crowd-low    { color: #22c55e; font-weight: 700; }
.crowd-medium { color: #f59e0b; font-weight: 700; }
.crowd-high   { color: #ef4444; font-weight: 700; }

/* ── TOP 3 CARDS ── */
.top3-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}
.run-card {
  border: 1px solid #e5e5e5;
  padding: 24px;
  position: relative;
  transition: border-color 0.2s;
}
.run-card:hover { border-color: #000; }
.rank-1 { border-top: 3px solid #FF4500; }
.rank-2 { border-top: 3px solid #888; }
.rank-3 { border-top: 3px solid #bbb; }

.card-rank {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #bbb;
  font-weight: 700;
  margin-bottom: 8px;
}
.card-name {
  font-size: 1.3rem;
  font-weight: 600;
  margin-bottom: 10px;
  line-height: 1.2;
}
.card-badges {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}
.card-score-row {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  padding: 12px 0;
  border-top: 1px solid #f0f0f0;
  border-bottom: 1px solid #f0f0f0;
}
.score-block { text-align: center; }
.score-val {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.5rem;
  font-weight: 700;
  color: #000;
}
.score-lbl {
  font-size: 0.7rem;
  color: #999;
  margin-top: 2px;
}
.card-surface {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #666;
  margin-bottom: 10px;
  text-transform: capitalize;
}
.card-reason {
  font-size: 0.9rem;
  line-height: 1.5;
  color: #333;
  margin-bottom: 12px;
  font-style: italic;
}
.card-meta {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #bbb;
}

/* ── STRATEGY ── */
.strategy-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2px;
  background: #e5e5e5;
}
.strategy-col {
  background: #fff;
  padding: 24px;
}
.strategy-slot {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  font-size: 1rem;
  letter-spacing: 1px;
  margin-bottom: 4px;
}
.strategy-time {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #FF4500;
  margin-bottom: 12px;
}
.strategy-rationale {
  font-size: 0.85rem;
  color: #555;
  line-height: 1.5;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}
.strategy-subsection { margin-bottom: 14px; }
.strategy-sub-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 1px;
  margin-bottom: 8px;
}
.strategy-sub-label.go    { color: #22c55e; }
.strategy-sub-label.avoid { color: #ef4444; }
.strategy-run {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid #f5f5f5;
  font-size: 0.85rem;
}
.sr-name { flex: 1; font-weight: 500; }
.sr-score {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  font-weight: 700;
  color: #FF4500;
}
.sr-surface {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #999;
  text-transform: capitalize;
}
.avoid-run .sr-name { color: #bbb; text-decoration: line-through; }

/* ── ITINERARY ── */
.itinerary-highlights {
  background: #f5f5f5;
  border-left: 3px solid #FF4500;
  padding: 12px 16px;
  font-size: 0.9rem;
  color: #333;
  margin-bottom: 24px;
  font-style: italic;
}
.itinerary-timeline {
  display: flex;
  flex-direction: column;
}
.itinerary-slot {
  display: flex;
  align-items: flex-start;
  gap: 0;
}
.it-time {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  font-weight: 700;
  color: #888;
  width: 52px;
  flex-shrink: 0;
  padding-top: 4px;
}
.it-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 24px;
  flex-shrink: 0;
}
.it-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid #000;
  flex-shrink: 0;
  margin-top: 4px;
}
.dot-lunch  { background: #f59e0b; border-color: #f59e0b; }
.it-dot.diff-green { background: #22c55e; border-color: #22c55e; }
.it-dot.diff-blue  { background: #3b82f6; border-color: #3b82f6; }
.it-dot.diff-red   { background: #ef4444; border-color: #ef4444; }
.it-dot.diff-black { background: #000; border-color: #000; }
.it-line {
  width: 2px;
  flex: 1;
  min-height: 20px;
  background: #e5e5e5;
  margin: 4px 0;
}
.it-content {
  padding: 2px 0 20px 16px;
  flex: 1;
}
.it-action {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 1px;
  color: #aaa;
  margin-bottom: 2px;
}
.lunch .it-action { color: #f59e0b; }
.it-run {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 6px;
}
.it-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}
.it-surface {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #888;
  text-transform: capitalize;
}
.it-enj {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  font-weight: 700;
  color: #FF4500;
}
.it-tip {
  font-size: 0.85rem;
  color: #555;
  font-style: italic;
  line-height: 1.4;
}

/* ── GEMS ── */
.gems-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}
.gem-card {
  border: 1px solid #e5e5e5;
  padding: 20px;
  border-top: 3px solid #FF4500;
}
.gem-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 10px;
}
.gem-name {
  font-size: 1.1rem;
  font-weight: 600;
}
.gem-alpha {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  font-weight: 700;
  color: #FF4500;
}
.gem-badges {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}
.gem-why { margin-bottom: 12px; }
.gem-why-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 1px;
  color: #888;
  margin-bottom: 4px;
}
.gem-why-label.excellent { color: #22c55e; }
.gem-why-text {
  font-size: 0.85rem;
  color: #444;
  line-height: 1.5;
}

/* ── SENSITIVITY ── */
.sensitivity-table {
  border: 1px solid #e5e5e5;
  margin-bottom: 24px;
}
.sens-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1fr;
  gap: 0;
  border-bottom: 1px solid #e5e5e5;
  padding: 10px 16px;
  align-items: center;
}
.sens-row:last-child { border-bottom: none; }
.sens-header {
  background: #f5f5f5;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 1px;
  color: #888;
}
.sens-var {
  font-size: 0.9rem;
  font-weight: 500;
}
.sens-num {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  text-align: right;
}
.sens-delta, .sens-pct {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  font-weight: 700;
  text-align: right;
}
.neg { color: #ef4444; }
.pos { color: #22c55e; }

.sensitivity-interps {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.interp-block {
  padding: 16px;
  background: #fafafa;
  border-left: 3px solid #e5e5e5;
}
.interp-var {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  font-weight: 700;
  color: #555;
  margin-bottom: 6px;
  letter-spacing: 0.5px;
}
.interp-text {
  font-size: 0.9rem;
  color: #444;
  line-height: 1.5;
}

/* ── STRESS TESTS ── */
.stress-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}
.stress-card {
  border: 1px solid #e5e5e5;
  padding: 20px;
}
.stress-name {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}
.stress-desc {
  font-size: 0.85rem;
  color: #666;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
  font-style: italic;
}
.stress-cols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 16px;
}
.stress-col {}
.stress-col-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 1px;
  margin-bottom: 8px;
}
.stress-col-label.go    { color: #22c55e; }
.stress-col-label.avoid { color: #ef4444; }
.stress-run {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 0;
  font-size: 0.8rem;
}
.stress-run.avoid .sr-name { color: #bbb; }
.stress-insight {
  background: #f5f5f5;
  padding: 10px 12px;
  font-size: 0.83rem;
  color: #444;
  line-height: 1.5;
  border-left: 3px solid #FF4500;
}
.insight-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  font-weight: 700;
  color: #FF4500;
  display: block;
  margin-bottom: 4px;
  letter-spacing: 1px;
}

/* ── DECISION RULES ── */
.rules-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.rule-card {
  display: flex;
  gap: 24px;
  padding: 20px;
  border: 1px solid #e5e5e5;
  align-items: flex-start;
}
.rule-num {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.5rem;
  font-weight: 700;
  color: #e5e5e5;
  flex-shrink: 0;
  width: 36px;
  line-height: 1;
}
.rule-body { flex: 1; }
.rule-condition {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: #555;
  margin-bottom: 6px;
  padding: 6px 10px;
  background: #f5f5f5;
  border-left: 2px solid #ccc;
}
.rule-action {
  font-size: 0.95rem;
  font-weight: 600;
  color: #000;
  margin-bottom: 8px;
  padding-left: 10px;
  border-left: 2px solid #FF4500;
}
.rule-rationale {
  font-size: 0.85rem;
  color: #555;
  line-height: 1.6;
  padding-left: 10px;
}

/* ── EMPTY STATE ── */
.empty-state {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  color: #999;
  padding: 24px;
  border: 1px dashed #e5e5e5;
  text-align: center;
}

/* ── SPLASH ── */
.splash {
  max-width: 600px;
  margin: 120px auto;
  text-align: center;
  padding: 0 32px;
}
.splash-icon { font-size: 4rem; margin-bottom: 16px; }
.splash-title {
  font-size: 2rem;
  font-weight: 600;
  margin-bottom: 16px;
}
.splash-sub {
  font-size: 1rem;
  color: #666;
  line-height: 1.6;
  margin-bottom: 12px;
}
.splash-season {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #aaa;
}

/* ── LOADING OVERLAY ── */
.loading-overlay {
  position: fixed;
  inset: 0;
  background: rgba(255,255,255,0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}
.loading-card {
  background: #fff;
  border: 1px solid #e5e5e5;
  padding: 48px 64px;
  text-align: center;
  box-shadow: 0 8px 32px rgba(0,0,0,0.1);
}
.loading-ski { font-size: 2.5rem; margin-bottom: 16px; }
.loading-text {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  color: #555;
  margin-bottom: 20px;
  letter-spacing: 1px;
}
.loading-bar {
  width: 200px;
  height: 3px;
  background: #e5e5e5;
  overflow: hidden;
}
.loading-fill {
  height: 100%;
  width: 40%;
  background: #FF4500;
  animation: slide 1.2s ease-in-out infinite;
}
@keyframes slide {
  0%   { transform: translateX(-100%); }
  50%  { transform: translateX(150%); }
  100% { transform: translateX(400%); }
}

/* ── RESPONSIVE ── */
@media (max-width: 1024px) {
  .top3-grid,
  .strategy-grid,
  .stress-grid,
  .gems-grid { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 768px) {
  .top3-grid,
  .strategy-grid,
  .stress-grid,
  .gems-grid { grid-template-columns: 1fr; }
  .controls-inner { flex-direction: column; align-items: flex-start; }
  .nav-right { display: none; }
  .sens-row { grid-template-columns: 2fr 1fr 1fr; }
  .sens-row span:nth-child(3),
  .sens-row span:nth-child(5) { display: none; }
}
</style>
