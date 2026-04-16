<template>
  <div class="cal">
    <div class="cal-grid" role="grid" aria-label="30-day content calendar">
      <div
        v-for="day in 30"
        :key="day"
        class="day"
        role="row"
      >
        <div class="day-head">
          <span class="day-num">{{ day }}</span>
          <span class="day-date">{{ dayDate(day) }}</span>
        </div>
        <div class="day-posts">
          <button
            v-for="post in postsForDay(day)"
            :key="post.id"
            type="button"
            :class="[
              'chip', post.platform,
              { flagged: post.revision_note, approved: post.is_approved }
            ]"
            @click="$emit('select-post', post)"
            :aria-label="`${post.platform} ${post.post_type}, day ${day}${post.is_approved ? ', approved' : post.revision_note ? ', revision requested' : ''}`"
          >
            <span class="chip-plat">{{ platformIcon(post.platform) }}</span>
            <span class="chip-type">{{ post.post_type }}</span>
            <span v-if="post.revision_note" class="chip-mark flag" aria-hidden="true">⚠</span>
            <span v-if="post.is_approved" class="chip-mark ok" aria-hidden="true">✓</span>
          </button>
        </div>
      </div>
    </div>

    <div class="legend" aria-hidden="true">
      <span class="ca-kicker">Legend</span>
      <span class="legend-item" data-k="educational">Educational</span>
      <span class="legend-item" data-k="promotional">Promotional</span>
      <span class="legend-item" data-k="engagement">Engagement</span>
      <span class="legend-item" data-k="story">Story</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  posts: { type: Array, default: () => [] },
})
defineEmits(['select-post'])

function postsForDay(day) {
  return props.posts.filter(p => p.day_number === day)
}

const startDate = computed(() => {
  if (!props.posts.length) return new Date()
  const sorted = [...props.posts].sort((a, b) => a.day_number - b.day_number)
  return new Date(sorted[0]?.scheduled_date || Date.now())
})

function dayDate(day) {
  const d = new Date(startDate.value)
  d.setDate(d.getDate() + day - 1)
  return d.toLocaleDateString('en-IE', { month: 'short', day: 'numeric' })
}

function platformIcon(platform) {
  return { linkedin: 'in', instagram: 'ig', facebook: 'fb', twitter: 'x' }[platform] || platform[0]
}
</script>

<style scoped>
.cal { width: 100%; }

.cal-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 1px;
  background: var(--hairline);
  border: 1px solid var(--hairline);
  border-radius: var(--r-3);
  overflow: hidden;
}

.day {
  display: flex; flex-direction: column;
  gap: var(--s-2);
  padding: var(--s-3);
  background: var(--paper);
  min-height: 108px;
  transition: background var(--dur-2) var(--ease-out);
}
.day:hover { background: var(--surface-1); }

.day-head {
  display: flex; align-items: baseline; justify-content: space-between;
  gap: 6px;
}
.day-num {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 1.125rem;
  letter-spacing: -0.02em;
  color: var(--ink-hi);
}
.day-date {
  font-family: var(--font-mono);
  font-size: var(--mono-cap);
  letter-spacing: 0.03em;
  color: var(--ink-lo);
}

.day-posts {
  display: flex; flex-direction: column; gap: 4px;
}

.chip {
  display: flex; align-items: center; gap: 6px;
  padding: 5px 8px;
  font-family: var(--font-mono);
  font-size: var(--mono-cap);
  letter-spacing: 0.03em;
  border: 1px solid transparent;
  border-radius: var(--r-1);
  cursor: pointer;
  background: var(--surface-1);
  color: var(--ink-mid);
  text-align: left;
  transition: transform var(--dur-2) var(--ease-out),
              border-color var(--dur-2) var(--ease-out);
}
.chip:hover {
  transform: translateX(1px);
  border-color: var(--ink-hi);
}
.chip:focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: 1px;
}

.chip.linkedin  { background: color-mix(in oklab, oklch(0.40 0.13 245), var(--paper) 90%); color: oklch(0.35 0.13 245); }
.chip.instagram { background: color-mix(in oklab, oklch(0.50 0.18 350), var(--paper) 92%); color: oklch(0.40 0.16 350); }
.chip.facebook  { background: color-mix(in oklab, oklch(0.42 0.15 260), var(--paper) 92%); color: oklch(0.35 0.14 260); }
.chip.twitter   { background: var(--surface-2); color: var(--ink-hi); }

.chip.flagged  { border-color: color-mix(in oklab, var(--flame), transparent 50%); }
.chip.approved { border-color: color-mix(in oklab, var(--ok), transparent 55%); }

.chip-plat {
  font-weight: 600;
  min-width: 16px;
}
.chip-type {
  flex: 1;
  text-transform: capitalize;
  font-weight: 500;
}
.chip-mark {
  font-family: var(--font-body);
  font-weight: 600;
  font-size: 0.7rem;
}
.chip-mark.flag { color: oklch(0.45 0.15 75); }
.chip-mark.ok   { color: var(--ok); }

.legend {
  display: flex; flex-wrap: wrap; gap: var(--s-3);
  align-items: center;
  margin-top: var(--s-5);
  font-size: var(--caption);
  color: var(--ink-lo);
}
.legend-item {
  font-family: var(--font-mono);
  letter-spacing: 0.04em;
  padding: 3px 10px;
  border-radius: var(--r-full);
  background: var(--surface-2);
}
</style>
