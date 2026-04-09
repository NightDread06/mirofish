<template>
  <div class="crowd-heatmap-card card">
    <h3>Crowd Heat Map</h3>
    <div class="heatmap-container">
      <svg class="heatmap" ref="heatmapSvg"></svg>
    </div>
    <div class="intensity-scale">
      <span class="label">Low</span>
      <div class="scale-bar"></div>
      <span class="label">High</span>
    </div>
  </div>
</template>

<script>
import * as d3 from 'd3';

export default {
  name: 'CrowdHeatmap',
  props: {
    runs: {
      type: Array,
      default: () => ['Run 1', 'Run 2', 'Run 3', 'Run 4', 'Run 5']
    },
    crowdData: {
      type: Array,
      default: () => []
    }
  },
  methods: {
    drawHeatmap() {
      if (!this.$refs.heatmapSvg) return;

      const svg = d3.select(this.$refs.heatmapSvg);
      svg.selectAll('*').remove();

      const margin = { top: 30, right: 20, bottom: 40, left: 100 };
      const cellSize = 30;
      const width = cellSize * 24 + margin.left + margin.right;
      const height = cellSize * this.runs.length + margin.top + margin.bottom;

      const g = svg
        .attr('width', width)
        .attr('height', height)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

      // Color scale
      const colorScale = d3.scaleLinear()
        .domain([0, 50, 100])
        .range(['#10b981', '#f59e0b', '#ef4444']);

      // Draw cells
      const data = this.generateHeatmapData();

      g.selectAll('rect')
        .data(data)
        .enter()
        .append('rect')
        .attr('x', d => d.hour * cellSize)
        .attr('y', d => this.runs.indexOf(d.run) * cellSize)
        .attr('width', cellSize - 1)
        .attr('height', cellSize - 1)
        .attr('fill', d => colorScale(d.crowd))
        .attr('rx', 2)
        .append('title')
        .text(d => `${d.run} - ${d.hour}:00 - Crowd: ${d.crowd}%`);

      // X axis (hours)
      const xScale = d3.scaleLinear()
        .domain([0, 23])
        .range([0, cellSize * 24]);

      g.append('g')
        .call(d3.axisTop(xScale).ticks(12).tickFormat(d => `${d}:00`))
        .style('font-size', '10px');

      // Y axis (runs)
      const yScale = d3.scaleBand()
        .domain(this.runs)
        .range([0, cellSize * this.runs.length]);

      g.append('g')
        .call(d3.axisLeft(yScale))
        .style('font-size', '12px');
    },
    generateHeatmapData() {
      const data = [];
      for (let runIdx = 0; runIdx < this.runs.length; runIdx++) {
        for (let hour = 0; hour < 24; hour++) {
          const crowd = this.crowdData[runIdx]?.[hour] !== undefined
            ? this.crowdData[runIdx][hour]
            : Math.round(Math.max(0, Math.min(100,
                (hour >= 9 && hour <= 16 ? 60 : 20) + (Math.random() * 30 - 15)
              )));
          data.push({
            run: this.runs[runIdx],
            hour,
            crowd
          });
        }
      }
      return data;
    }
  },
  mounted() {
    this.drawHeatmap();
  },
  watch: {
    crowdData: {
      handler() {
        this.$nextTick(() => this.drawHeatmap());
      },
      deep: true
    },
    runs: {
      handler() {
        this.$nextTick(() => this.drawHeatmap());
      },
      deep: true
    }
  }
};
</script>

<style scoped>
.crowd-heatmap-card {
  width: 100%;
}

.heatmap-container {
  overflow-x: auto;
  margin: var(--spacing-md) 0;
  -webkit-overflow-scrolling: touch;
}

.heatmap {
  display: block;
  margin: 0 auto;
}

.intensity-scale {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
  font-size: var(--font-size-sm);
}

.scale-bar {
  flex: 1;
  height: 20px;
  background: linear-gradient(to right, #10b981, #f59e0b, #ef4444);
  border-radius: var(--border-radius);
}

.label {
  color: var(--text-secondary);
}
</style>
