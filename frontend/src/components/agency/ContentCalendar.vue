<template>
  <div class="content-calendar">
    <div class="calendar-grid">
      <div
        v-for="day in 30"
        :key="day"
        class="day-cell"
      >
        <div class="day-label">Day {{ day }}</div>
        <div class="day-date">{{ dayDate(day) }}</div>
        <div class="posts-in-day">
          <div
            v-for="post in postsForDay(day)"
            :key="post.id"
            :class="['post-chip', post.platform, post.post_type, { flagged: post.revision_note, approved: post.is_approved }]"
            @click="$emit('select-post', post)"
            :title="`${post.platform} · ${post.post_type}`"
          >
            <span class="chip-platform">{{ platformIcon(post.platform) }}</span>
            <span class="chip-type">{{ post.post_type }}</span>
            <span v-if="post.revision_note" class="chip-flag" title="Revision requested">⚠</span>
            <span v-if="post.is_approved" class="chip-approved" title="Approved">✓</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Legend -->
    <div class="legend">
      <span class="legend-title">Post types:</span>
      <span class="legend-item educational">Educational</span>
      <span class="legend-item promotional">Promotional</span>
      <span class="legend-item engagement">Engagement</span>
      <span class="legend-item story">Story</span>
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
  const icons = { linkedin: 'in', instagram: '📸', facebook: 'fb', twitter: '𝕏' }
  return icons[platform] || platform[0].toUpperCase()
}
</script>

<style scoped>
.content-calendar { width: 100%; }

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 8px;
}

.day-cell {
  border: 1px solid #e0e0e0;
  padding: 10px;
  background: #fff;
  min-height: 100px;
}

.day-label {
  font-size: 0.7rem;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #999;
  margin-bottom: 2px;
}

.day-date {
  font-size: 0.8rem;
  color: #555;
  margin-bottom: 8px;
}

.posts-in-day {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.post-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 6px;
  font-size: 0.7rem;
  cursor: pointer;
  border: 1px solid transparent;
  border-radius: 2px;
  transition: opacity 0.1s;
  user-select: none;
}
.post-chip:hover { opacity: 0.75; }

/* Platform colours */
.post-chip.linkedin   { background: #e8f0f8; border-color: #b0c8e8; }
.post-chip.instagram  { background: #fce8f4; border-color: #e8b0d0; }
.post-chip.facebook   { background: #e8ecf8; border-color: #b0bce8; }
.post-chip.twitter    { background: #e8f4fc; border-color: #b0d8ec; }

/* Post type tint */
.post-chip.educational  { opacity: 0.9; }
.post-chip.promotional  { font-weight: bold; }
.post-chip.engagement   { font-style: italic; }

/* State indicators */
.post-chip.flagged  { border-color: #f90; }
.post-chip.approved { border-color: #090; }

.chip-platform { font-weight: bold; font-size: 0.68rem; }
.chip-type { flex: 1; font-size: 0.68rem; text-transform: capitalize; color: #555; }
.chip-flag { color: #f90; }
.chip-approved { color: #090; }

/* Legend */
.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  margin-top: 20px;
  font-size: 0.8rem;
}
.legend-title { font-weight: bold; color: #555; }
.legend-item {
  padding: 2px 10px;
  border-radius: 2px;
  font-size: 0.75rem;
}
.legend-item.educational { background: #e8f0f8; }
.legend-item.promotional { background: #ffe0e0; font-weight: bold; }
.legend-item.engagement  { background: #e8fce8; font-style: italic; }
.legend-item.story       { background: #fef8e0; }
</style>
