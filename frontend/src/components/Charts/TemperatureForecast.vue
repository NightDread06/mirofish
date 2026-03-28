<template>
  <div class="temperature-card card">
    <h3>8-Day Temperature Forecast</h3>
    <div class="chart-container">
      <svg class="chart" ref="temperatureChart"></svg>
    </div>
    <div class="legend">
      <div class="legend-item">
        <span class="line-sample high"></span>
        <span>High</span>
      </div>
      <div class="legend-item">
        <span class="line-sample low"></span>
        <span>Low</span>
      </div>
    </div>
  </div>
</template>

<script>
import * as d3 from 'd3';

export default {
  name: 'TemperatureForecast',
  props: {
    forecast: {
      type: Array,
      default: () => [
        { day: 'Mon', high: -2, low: -8 },
        { day: 'Tue', high: 0, low: -6 },
        { day: 'Wed', high: 3, low: -4 },
        { day: 'Thu', high: -1, low: -7 },
        { day: 'Fri', high: -3, low: -9 },
        { day: 'Sat', high: 1, low: -5 },
        { day: 'Sun', high: 2, low: -5 },
        { day: 'Mon', high: -2, low: -8 }
      ]
    }
  },
  methods: {
    drawChart() {
      if (!this.$refs.temperatureChart) return;

      const svg = d3.select(this.$refs.temperatureChart);
      svg.selectAll('*').remove();

      const margin = { top: 20, right: 20, bottom: 30, left: 60 };
      const width = 400 - margin.left - margin.right;
      const height = 250 - margin.top - margin.bottom;

      const g = svg
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

      // Scales
      const xScale = d3.scaleBand()
        .domain(this.forecast.map(d => d.day))
        .range([0, width])
        .padding(0.1);

      const allTemps = this.forecast.flatMap(d => [d.high, d.low]);
      const yMin = Math.min(...allTemps) - 2;
      const yMax = Math.max(...allTemps) + 2;

      const yScale = d3.scaleLinear()
        .domain([yMin, yMax])
        .range([height, 0]);

      // Area between
      const area = d3.area()
        .x(d => xScale(d.day) + xScale.bandwidth() / 2)
        .y0(d => yScale(d.low))
        .y1(d => yScale(d.high));

      g.append('path')
        .datum(this.forecast)
        .attr('fill', 'rgba(59, 130, 246, 0.15)')
        .attr('d', area);

      // High line
      const highLine = d3.line()
        .x(d => xScale(d.day) + xScale.bandwidth() / 2)
        .y(d => yScale(d.high));

      g.append('path')
        .datum(this.forecast)
        .attr('fill', 'none')
        .attr('stroke', '#3b82f6')
        .attr('stroke-width', 2)
        .attr('d', highLine);

      // High dots
      g.selectAll('.dot-high')
        .data(this.forecast)
        .enter()
        .append('circle')
        .attr('class', 'dot-high')
        .attr('cx', d => xScale(d.day) + xScale.bandwidth() / 2)
        .attr('cy', d => yScale(d.high))
        .attr('r', 4)
        .attr('fill', '#3b82f6');

      // Low line
      const lowLine = d3.line()
        .x(d => xScale(d.day) + xScale.bandwidth() / 2)
        .y(d => yScale(d.low));

      g.append('path')
        .datum(this.forecast)
        .attr('fill', 'none')
        .attr('stroke', '#60a5fa')
        .attr('stroke-width', 2)
        .attr('stroke-dasharray', '5,5')
        .attr('d', lowLine);

      // Low dots
      g.selectAll('.dot-low')
        .data(this.forecast)
        .enter()
        .append('circle')
        .attr('class', 'dot-low')
        .attr('cx', d => xScale(d.day) + xScale.bandwidth() / 2)
        .attr('cy', d => yScale(d.low))
        .attr('r', 4)
        .attr('fill', '#60a5fa');

      // X axis
      g.append('g')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(xScale));

      // Y axis
      g.append('g')
        .call(d3.axisLeft(yScale).ticks(5).tickFormat(d => `${d}°`))
        .append('text')
        .attr('fill', 'var(--text-secondary)')
        .attr('transform', 'rotate(-90)')
        .attr('y', -50)
        .attr('x', -height / 2)
        .attr('text-anchor', 'middle')
        .text('Temperature (°C)');

      // Freeze line
      if (yMin <= 0 && yMax >= 0) {
        g.append('line')
          .attr('x1', 0)
          .attr('x2', width)
          .attr('y1', yScale(0))
          .attr('y2', yScale(0))
          .attr('stroke', '#ef4444')
          .attr('stroke-width', 1)
          .attr('stroke-dasharray', '3,3')
          .attr('opacity', 0.5);
      }
    }
  },
  mounted() {
    this.drawChart();
  },
  watch: {
    forecast: {
      handler() {
        this.$nextTick(() => this.drawChart());
      },
      deep: true
    }
  }
};
</script>

<style scoped>
.temperature-card {
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
  display: flex;
  gap: var(--spacing-lg);
  justify-content: center;
  margin-top: var(--spacing-sm);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.line-sample {
  display: inline-block;
  width: 24px;
  height: 2px;
}

.line-sample.high {
  background: #3b82f6;
}

.line-sample.low {
  background: #60a5fa;
  background-image: repeating-linear-gradient(
    90deg,
    #60a5fa 0px,
    #60a5fa 5px,
    transparent 5px,
    transparent 10px
  );
}

@media (max-width: 768px) {
  .chart {
    max-width: 100%;
  }
}
</style>
