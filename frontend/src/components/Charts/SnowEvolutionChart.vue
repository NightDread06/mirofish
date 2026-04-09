<template>
  <div class="snow-evolution-card card">
    <h3>Snow Evolution by Orientation</h3>
    <div class="chart-container">
      <svg class="chart" ref="chartSvg"></svg>
    </div>
    <div class="legend">
      <div v-for="orientation in orientations" :key="orientation" class="legend-item">
        <span class="color-dot" :style="{ backgroundColor: getOrientationColor(orientation) }"></span>
        <span>{{ orientation }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import * as d3 from 'd3';

export default {
  name: 'SnowEvolutionChart',
  props: {
    data: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      orientations: ['North', 'Northeast', 'East', 'Southeast', 'South', 'Southwest', 'West', 'Northwest']
    };
  },
  methods: {
    getOrientationColor(orientation) {
      const colors = {
        'North': '#1e3a8a',
        'Northeast': '#3b82f6',
        'East': '#60a5fa',
        'Southeast': '#93c5fd',
        'South': '#fbbf24',
        'Southwest': '#fb923c',
        'West': '#f97316',
        'Northwest': '#991b1b'
      };
      return colors[orientation] || '#666';
    },
    drawChart() {
      if (!this.$refs.chartSvg) return;

      const svg = d3.select(this.$refs.chartSvg);
      svg.selectAll('*').remove();

      const margin = { top: 20, right: 20, bottom: 40, left: 60 };
      const width = 400 - margin.left - margin.right;
      const height = 300 - margin.top - margin.bottom;

      const g = svg
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

      // X scale (hours)
      const xScale = d3.scaleLinear()
        .domain([0, 24])
        .range([0, width]);

      // Y scale (snow depth)
      const yScale = d3.scaleLinear()
        .domain([0, 100])
        .range([height, 0]);

      // Line generator
      const line = d3.line()
        .x((d, i) => xScale(i))
        .y(d => yScale(d));

      // Draw lines for each orientation
      this.orientations.forEach((orientation) => {
        const HOURS_COUNT = 25;
        const INITIAL_SNOW_DEPTH = 80;
        const MELT_RATE = 2;
        const NOISE_RANGE = 10;
        const values = this.data.length > 0
          ? this.data.map(d => d[orientation] || 50)
          : Array.from({ length: HOURS_COUNT }, (_, i) =>
              Math.max(0, INITIAL_SNOW_DEPTH - i * MELT_RATE + (Math.random() * NOISE_RANGE - NOISE_RANGE / 2))
            );

        g.append('path')
          .datum(values)
          .attr('fill', 'none')
          .attr('stroke', this.getOrientationColor(orientation))
          .attr('stroke-width', 2)
          .attr('d', line);
      });

      // X axis
      g.append('g')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(xScale).ticks(6))
        .append('text')
        .attr('fill', 'var(--text-primary)')
        .attr('x', width / 2)
        .attr('y', 35)
        .attr('text-anchor', 'middle')
        .text('Hours');

      // Y axis
      g.append('g')
        .call(d3.axisLeft(yScale).ticks(5))
        .append('text')
        .attr('fill', 'var(--text-primary)')
        .attr('transform', 'rotate(-90)')
        .attr('y', -50)
        .attr('x', -height / 2)
        .attr('text-anchor', 'middle')
        .text('Snow Depth (cm)');
    }
  },
  watch: {
    data: {
      handler() {
        this.$nextTick(() => this.drawChart());
      },
      deep: true
    }
  },
  mounted() {
    this.drawChart();
  }
};
</script>

<style scoped>
.snow-evolution-card {
  width: 100%;
}

.chart-container {
  display: flex;
  justify-content: center;
  margin: var(--spacing-md) 0;
  overflow-x: auto;
}

.chart {
  min-width: 100%;
  height: auto;
}

.legend {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.color-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .chart {
    max-width: 100%;
  }

  .legend {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
