<template>
  <div class="stress-test-card card">
    <h3>Scenario Analysis</h3>
    <div class="scenarios-container">
      <div v-for="scenario in scenarios" :key="scenario.name" class="scenario">
        <h4>{{ scenario.name }}</h4>
        <div class="chart-mini">
          <svg :ref="el => { if (el) chartRefs[scenario.name] = el }" class="mini-chart"></svg>
        </div>
        <div class="metrics">
          <div class="metric">
            <span class="label">Snow Quality:</span>
            <span class="value" :style="{ color: getMetricColor(scenario.snowQuality) }">
              {{ scenario.snowQuality }}%
            </span>
          </div>
          <div class="metric">
            <span class="label">Crowd Level:</span>
            <span class="value" :style="{ color: getMetricColor(100 - scenario.crowd) }">
              {{ scenario.crowd }}%
            </span>
          </div>
          <div class="metric">
            <span class="label">Enjoyment:</span>
            <span class="value" :style="{ color: getMetricColor(scenario.enjoyment * 10) }">
              {{ scenario.enjoyment }}/10
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as d3 from 'd3';

export default {
  name: 'StressTestComparison',
  props: {
    scenarios: {
      type: Array,
      default: () => [
        { name: 'Warm Spell', snowQuality: 45, crowd: 75, enjoyment: 5 },
        { name: 'Peak Crowds', snowQuality: 70, crowd: 95, enjoyment: 4 },
        { name: 'Snow Drought', snowQuality: 25, crowd: 40, enjoyment: 3 },
        { name: 'Perfect Day', snowQuality: 95, crowd: 50, enjoyment: 9 }
      ]
    }
  },
  data() {
    return {
      chartRefs: {}
    };
  },
  methods: {
    getMetricColor(value) {
      if (value >= 80) return 'var(--color-success)';
      if (value >= 60) return 'var(--color-warning)';
      return 'var(--color-danger)';
    },
    drawScenarioChart(scenario) {
      const el = this.chartRefs[scenario.name];
      if (!el) return;

      const values = [scenario.snowQuality, scenario.crowd, scenario.enjoyment * 10];
      const labels = ['Snow', 'Crowd', 'Enjoy'];

      const svg = d3.select(el);
      svg.selectAll('*').remove();

      const width = 150;
      const height = 100;
      const margin = { top: 10, right: 10, bottom: 20, left: 10 };
      const barWidth = (width - margin.left - margin.right) / values.length;

      const yScale = d3.scaleLinear()
        .domain([0, 100])
        .range([height - margin.bottom, margin.top]);

      const g = svg
        .attr('width', width)
        .attr('height', height)
        .append('g');

      g.selectAll('rect')
        .data(values)
        .enter()
        .append('rect')
        .attr('x', (d, i) => i * barWidth + margin.left)
        .attr('y', d => yScale(d))
        .attr('width', barWidth - 4)
        .attr('height', d => height - margin.bottom - yScale(d))
        .attr('fill', d => {
          if (d >= 80) return 'var(--color-success)';
          if (d >= 60) return 'var(--color-warning)';
          return 'var(--color-danger)';
        })
        .attr('rx', 3);

      g.selectAll('text.label')
        .data(labels)
        .enter()
        .append('text')
        .attr('class', 'label')
        .attr('x', (d, i) => i * barWidth + margin.left + (barWidth - 4) / 2)
        .attr('y', height - 4)
        .attr('text-anchor', 'middle')
        .attr('font-size', '9px')
        .attr('fill', 'var(--text-secondary)')
        .text(d => d);
    },
    drawAllCharts() {
      this.scenarios.forEach(s => this.drawScenarioChart(s));
    }
  },
  watch: {
    scenarios: {
      handler() {
        this.$nextTick(() => this.drawAllCharts());
      },
      deep: true
    }
  },
  mounted() {
    this.$nextTick(() => this.drawAllCharts());
  }
};
</script>

<style scoped>
.stress-test-card {
  width: 100%;
}

.scenarios-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-lg);
  margin-top: var(--spacing-md);
}

.scenario {
  background: var(--bg-tertiary);
  padding: var(--spacing-md);
  border-radius: var(--border-radius);
  border: 1px solid var(--border-color);
}

.scenario h4 {
  margin-bottom: var(--spacing-md);
  color: var(--text-primary);
}

.chart-mini {
  display: flex;
  justify-content: center;
  margin-bottom: var(--spacing-md);
}

.mini-chart {
  max-width: 100%;
}

.metrics {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.metric {
  display: flex;
  justify-content: space-between;
  font-size: var(--font-size-sm);
}

.label {
  color: var(--text-secondary);
}

.value {
  font-weight: 600;
}

@media (max-width: 768px) {
  .scenarios-container {
    grid-template-columns: 1fr;
  }
}
</style>
