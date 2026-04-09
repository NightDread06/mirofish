<template>
  <div class="dashboard">
    <!-- Header -->
    <header class="dashboard-header">
      <div class="header-brand">
        <span class="ski-icon">⛷️</span>
        <div>
          <h1 class="brand-title">Ski Dashboard</h1>
          <p class="brand-subtitle">Avoriaz / Portes du Soleil</p>
        </div>
      </div>
      <div class="header-controls">
        <div class="refresh-info hidden-mobile">
          <span class="refresh-dot" :class="{ refreshing: isRefreshing }"></span>
          <span class="refresh-text">{{ lastUpdatedText }}</span>
        </div>
        <button class="btn secondary refresh-btn" @click="refreshData" :disabled="isRefreshing">
          <span v-if="isRefreshing">↻ Refreshing…</span>
          <span v-else>↻ Refresh</span>
        </button>
        <ThemeToggle />
      </div>
    </header>

    <!-- Loading state -->
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <p>Loading ski conditions…</p>
    </div>

    <!-- Main content -->
    <main v-else class="dashboard-content container">

      <!-- Status Cards Row -->
      <section class="section">
        <div class="grid grid-4">
          <div class="card compact stat-card">
            <div class="stat-icon">🌨️</div>
            <div class="stat-body">
              <p class="stat-label">Snow Depth</p>
              <p class="stat-value">{{ conditions.snowDepth ?? '–' }} cm</p>
              <span class="badge" :class="snowBadgeClass">{{ snowQualityLabel }}</span>
            </div>
          </div>
          <div class="card compact stat-card">
            <div class="stat-icon">🌡️</div>
            <div class="stat-body">
              <p class="stat-label">Temperature</p>
              <p class="stat-value">{{ conditions.temperature ?? '–' }}°C</p>
              <span class="badge info">Summit</span>
            </div>
          </div>
          <div class="card compact stat-card">
            <div class="stat-icon">👥</div>
            <div class="stat-body">
              <p class="stat-label">Crowd Level</p>
              <p class="stat-value">{{ conditions.crowdLevel ?? '–' }}%</p>
              <span class="badge" :class="crowdBadgeClass">{{ crowdLabel }}</span>
            </div>
          </div>
          <div class="card compact stat-card">
            <div class="stat-icon">💨</div>
            <div class="stat-body">
              <p class="stat-label">Wind Speed</p>
              <p class="stat-value">{{ conditions.windSpeed ?? '–' }} km/h</p>
              <span class="badge" :class="windBadgeClass">{{ windLabel }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Recommendation Banner -->
      <section class="section" v-if="recommendation">
        <div class="card recommendation-card">
          <div class="rec-header">
            <h2>Today's Recommendation</h2>
            <span class="badge success">AI Powered</span>
          </div>
          <p class="rec-text">{{ recommendation.summary }}</p>
          <div class="rec-runs" v-if="recommendation.runs && recommendation.runs.length">
            <h4>Best Runs Today</h4>
            <div class="runs-list">
              <div v-for="run in recommendation.runs" :key="run.name" class="run-chip">
                <span class="run-name">{{ run.name }}</span>
                <span class="badge success">{{ run.score }}/10</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Charts Row 1 -->
      <section class="section">
        <div class="grid grid-3" style="grid-template-columns: 1fr 1fr;">
          <TemperatureForecast :forecast="temperatureForecast" />
          <SnowEvolutionChart :data="snowEvolutionData" />
        </div>
      </section>

      <!-- Charts Row 2 -->
      <section class="section">
        <CrowdHeatmap :runs="runNames" :crowdData="crowdHeatmapData" />
      </section>

      <!-- Charts Row 3 -->
      <section class="section">
        <StressTestComparison :scenarios="scenarios" />
      </section>

      <!-- Auto-refresh footer -->
      <footer class="dashboard-footer">
        <p>Data refreshes automatically every 10 minutes. Last updated: {{ lastUpdatedText }}</p>
      </footer>
    </main>
  </div>
</template>

<script>
import ThemeToggle from './ThemeToggle.vue';
import TemperatureForecast from './Charts/TemperatureForecast.vue';
import SnowEvolutionChart from './Charts/SnowEvolutionChart.vue';
import CrowdHeatmap from './Charts/CrowdHeatmap.vue';
import StressTestComparison from './Charts/StressTestComparison.vue';

const REFRESH_INTERVAL_MS = 10 * 60 * 1000; // 10 minutes

export default {
  name: 'Dashboard',
  components: {
    ThemeToggle,
    TemperatureForecast,
    SnowEvolutionChart,
    CrowdHeatmap,
    StressTestComparison
  },
  data() {
    return {
      loading: true,
      isRefreshing: false,
      lastUpdated: null,
      refreshTimer: null,

      // Ski conditions
      conditions: {
        snowDepth: null,
        temperature: null,
        crowdLevel: null,
        windSpeed: null
      },

      // Recommendation from AI engine
      recommendation: null,

      // Chart data
      temperatureForecast: [
        { day: 'Mon', high: -2, low: -8 },
        { day: 'Tue', high: 0, low: -6 },
        { day: 'Wed', high: 3, low: -4 },
        { day: 'Thu', high: -1, low: -7 },
        { day: 'Fri', high: -3, low: -9 },
        { day: 'Sat', high: 1, low: -5 },
        { day: 'Sun', high: 2, low: -5 },
        { day: 'Mon', high: -2, low: -8 }
      ],
      snowEvolutionData: [],
      crowdHeatmapData: [],
      runNames: ['Avoriaz Main', 'Les Lindarets', 'Morzine Blue', 'Super Morzine', 'Châtel Red'],
      scenarios: [
        { name: 'Warm Spell', snowQuality: 45, crowd: 75, enjoyment: 5 },
        { name: 'Peak Crowds', snowQuality: 70, crowd: 95, enjoyment: 4 },
        { name: 'Snow Drought', snowQuality: 25, crowd: 40, enjoyment: 3 },
        { name: 'Perfect Day', snowQuality: 95, crowd: 50, enjoyment: 9 }
      ]
    };
  },
  computed: {
    lastUpdatedText() {
      if (!this.lastUpdated) return 'Never';
      const diff = Math.round((Date.now() - this.lastUpdated) / 1000);
      if (diff < 60) return `${diff}s ago`;
      if (diff < 3600) return `${Math.round(diff / 60)}m ago`;
      return new Date(this.lastUpdated).toLocaleTimeString();
    },
    snowBadgeClass() {
      const d = this.conditions.snowDepth;
      if (d == null) return 'info';
      if (d >= 80) return 'success';
      if (d >= 40) return 'warning';
      return 'danger';
    },
    snowQualityLabel() {
      const d = this.conditions.snowDepth;
      if (d == null) return 'Unknown';
      if (d >= 80) return 'Excellent';
      if (d >= 40) return 'Good';
      return 'Poor';
    },
    crowdBadgeClass() {
      const c = this.conditions.crowdLevel;
      if (c == null) return 'info';
      if (c <= 40) return 'success';
      if (c <= 70) return 'warning';
      return 'danger';
    },
    crowdLabel() {
      const c = this.conditions.crowdLevel;
      if (c == null) return 'Unknown';
      if (c <= 40) return 'Low';
      if (c <= 70) return 'Moderate';
      return 'High';
    },
    windBadgeClass() {
      const w = this.conditions.windSpeed;
      if (w == null) return 'info';
      if (w <= 20) return 'success';
      if (w <= 40) return 'warning';
      return 'danger';
    },
    windLabel() {
      const w = this.conditions.windSpeed;
      if (w == null) return 'Unknown';
      if (w <= 20) return 'Calm';
      if (w <= 40) return 'Moderate';
      return 'Strong';
    }
  },
  methods: {
    async fetchData() {
      try {
        // Attempt to fetch from backend API
        const response = await fetch('/api/ski/conditions').catch(() => null);
        if (response && response.ok) {
          const data = await response.json();
          this.conditions = {
            snowDepth: data.snow_depth ?? data.snowDepth ?? this.conditions.snowDepth,
            temperature: data.temperature ?? this.conditions.temperature,
            crowdLevel: data.crowd_level ?? data.crowdLevel ?? this.conditions.crowdLevel,
            windSpeed: data.wind_speed ?? data.windSpeed ?? this.conditions.windSpeed
          };
          if (data.recommendation) {
            this.recommendation = data.recommendation;
          }
          if (data.temperature_forecast) {
            this.temperatureForecast = data.temperature_forecast;
          }
          if (data.snow_evolution) {
            this.snowEvolutionData = data.snow_evolution;
          }
          if (data.crowd_heatmap) {
            this.crowdHeatmapData = data.crowd_heatmap;
          }
        } else {
          // Use demo data when API is unavailable
          this.loadDemoData();
        }
      } catch {
        this.loadDemoData();
      }
      this.lastUpdated = Date.now();
    },
    loadDemoData() {
      this.conditions = {
        snowDepth: 95,
        temperature: -4,
        crowdLevel: 55,
        windSpeed: 18
      };
      this.recommendation = {
        summary: 'Great conditions today! Fresh snow overnight with light winds. Best time to ski is early morning (8-11am) before crowds build. Recommend heading to north-facing runs for the best powder.',
        runs: [
          { name: 'Avoriaz Main', score: 9 },
          { name: 'Les Lindarets', score: 8 },
          { name: 'Super Morzine', score: 8 }
        ]
      };
    },
    async refreshData() {
      if (this.isRefreshing) return;
      this.isRefreshing = true;
      try {
        await this.fetchData();
      } finally {
        this.isRefreshing = false;
      }
    },
    startAutoRefresh() {
      this.refreshTimer = setInterval(() => this.refreshData(), REFRESH_INTERVAL_MS);
    },
    stopAutoRefresh() {
      if (this.refreshTimer) {
        clearInterval(this.refreshTimer);
        this.refreshTimer = null;
      }
    }
  },
  async mounted() {
    await this.fetchData();
    this.loading = false;
    this.startAutoRefresh();
  },
  beforeUnmount() {
    this.stopAutoRefresh();
  }
};
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  background: var(--bg-primary);
  color: var(--text-primary);
}

/* Header */
.dashboard-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  padding: var(--spacing-md) var(--spacing-lg);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  box-shadow: var(--shadow-sm);
}

.header-brand {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.ski-icon {
  font-size: 2rem;
}

.brand-title {
  font-size: var(--font-size-xl);
  font-weight: 700;
  margin-bottom: 0;
  color: var(--text-primary);
}

.brand-subtitle {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.2;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.refresh-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.refresh-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-success);
  flex-shrink: 0;
}

.refresh-dot.refreshing {
  background: var(--color-warning);
  animation: pulse 1s infinite;
}

@keyframes pulse {
  50% { opacity: 0.4; }
}

.refresh-btn {
  white-space: nowrap;
}

/* Loading */
.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  gap: var(--spacing-lg);
  color: var(--text-secondary);
}

/* Content */
.dashboard-content {
  padding-top: var(--spacing-lg);
  padding-bottom: var(--spacing-2xl);
}

.section {
  margin-bottom: var(--spacing-lg);
}

/* Stat Cards */
.stat-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.stat-icon {
  font-size: 2rem;
  flex-shrink: 0;
}

.stat-body {
  flex: 1;
  min-width: 0;
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.2;
}

.stat-value {
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: var(--spacing-xs) 0;
  line-height: 1.2;
}

/* Recommendation */
.recommendation-card {
  background: linear-gradient(135deg, var(--bg-secondary), var(--bg-tertiary));
}

.rec-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-md);
}

.rec-header h2 {
  margin-bottom: 0;
}

.rec-text {
  color: var(--text-secondary);
  margin-bottom: var(--spacing-lg);
  font-size: var(--font-size-base);
  line-height: 1.6;
}

.rec-runs h4 {
  margin-bottom: var(--spacing-sm);
  color: var(--text-primary);
}

.runs-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.run-chip {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: var(--spacing-xs) var(--spacing-sm);
  font-size: var(--font-size-sm);
}

.run-name {
  color: var(--text-primary);
  font-weight: 500;
}

/* Footer */
.dashboard-footer {
  text-align: center;
  padding: var(--spacing-lg) 0;
  border-top: 1px solid var(--border-color);
  margin-top: var(--spacing-xl);
}

.dashboard-footer p {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  margin: 0;
}

/* Responsive overrides */
@media (max-width: 768px) {
  .dashboard-header {
    padding: var(--spacing-sm) var(--spacing-md);
  }

  .brand-title {
    font-size: var(--font-size-lg);
  }

  .ski-icon {
    font-size: 1.5rem;
  }

  .rec-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-sm);
  }
}

@media (max-width: 640px) {
  /* Stack the two-column chart grid on mobile */
  .section .grid[style*="grid-template-columns: 1fr 1fr"] {
    grid-template-columns: 1fr !important;
  }
}
</style>
