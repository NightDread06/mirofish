<template>
  <div class="post-card">
    <!-- Header -->
    <div class="post-header">
      <div class="post-meta">
        <span class="platform-badge" :class="post.platform">
          {{ platformLabel(post.platform) }}
        </span>
        <span class="type-badge" :class="post.post_type">{{ post.post_type }}</span>
        <span class="day-badge">Day {{ post.day_number }}</span>
        <span class="date-label">{{ formatDate(post.scheduled_date) }}</span>
      </div>
      <div class="post-status">
        <span v-if="post.is_approved" class="status approved">✓ Approved</span>
        <span v-else-if="post.revision_note" class="status revision">⚠ Revision requested</span>
      </div>
    </div>

    <!-- Copy -->
    <div class="post-section">
      <div class="section-label">
        Post copy
        <button class="copy-btn" @click="copyText(post.post_copy)" :class="{ copied: copiedField === 'copy' }">
          {{ copiedField === 'copy' ? 'Copied!' : 'Copy' }}
        </button>
      </div>
      <p class="post-copy">{{ post.post_copy }}</p>
    </div>

    <!-- Hashtags -->
    <div v-if="post.hashtags" class="post-section">
      <div class="section-label">
        Hashtags
        <button class="copy-btn" @click="copyText(post.hashtags)" :class="{ copied: copiedField === 'hashtags' }">
          {{ copiedField === 'hashtags' ? 'Copied!' : 'Copy' }}
        </button>
      </div>
      <p class="hashtag-line">{{ post.hashtags }}</p>
    </div>

    <!-- CTA -->
    <div v-if="post.call_to_action" class="post-section">
      <div class="section-label">Call to action</div>
      <p class="cta-text">{{ post.call_to_action }}</p>
    </div>

    <!-- Visual description -->
    <div v-if="post.visual_description" class="post-section">
      <div class="section-label">Visual direction</div>
      <p class="visual-text">{{ post.visual_description }}</p>
    </div>

    <!-- Revision note (if present) -->
    <div v-if="post.revision_note" class="revision-note">
      <strong>Revision note:</strong> {{ post.revision_note }}
    </div>

    <!-- Actions -->
    <div class="post-actions">
      <button class="btn-primary" @click="copyAll">Copy All Text</button>
      <button v-if="!post.is_approved" class="btn-outline" @click="$emit('approve', post)">
        Mark Approved
      </button>
      <button class="btn-ghost" @click="$emit('request-revision', post)">
        Request Revision
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useClipboard } from '@vueuse/core'

const props = defineProps({
  post: { type: Object, required: true },
})
defineEmits(['approve', 'request-revision'])

const { copy } = useClipboard()
const copiedField = ref('')

function platformLabel(p) {
  return { linkedin: 'LinkedIn', instagram: 'Instagram', facebook: 'Facebook', twitter: 'X (Twitter)' }[p] || p
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('en-IE', { weekday: 'short', day: 'numeric', month: 'short' })
}

async function copyText(text) {
  await copy(text)
}

async function copyText(text, field) {
  await copy(text)
  copiedField.value = field
  setTimeout(() => { copiedField.value = '' }, 2000)
}

async function copyAll() {
  const parts = []
  if (props.post.post_copy) parts.push(props.post.post_copy)
  if (props.post.hashtags) parts.push(props.post.hashtags)
  if (props.post.call_to_action) parts.push(props.post.call_to_action)
  await copy(parts.join('\n\n'))
  copiedField.value = 'all'
  setTimeout(() => { copiedField.value = '' }, 2000)
}
</script>

<style scoped>
.post-card { font-family: 'Courier New', monospace; }

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 8px;
}
.post-meta { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.platform-badge {
  padding: 4px 10px;
  font-size: 0.78rem;
  font-weight: bold;
  border: 1px solid;
}
.platform-badge.linkedin  { color: #0077b5; border-color: #0077b5; background: #e8f0f8; }
.platform-badge.instagram { color: #c13584; border-color: #c13584; background: #fce8f4; }
.platform-badge.facebook  { color: #1877f2; border-color: #1877f2; background: #e8ecf8; }
.platform-badge.twitter   { color: #111; border-color: #111; background: #f0f0f0; }

.type-badge { padding: 4px 10px; font-size: 0.78rem; background: #f0f0f0; border: 1px solid #ddd; }
.day-badge  { font-size: 0.78rem; font-weight: bold; }
.date-label { font-size: 0.78rem; color: #888; }

.post-status { font-size: 0.82rem; }
.status.approved  { color: #090; font-weight: bold; }
.status.revision  { color: #f90; font-weight: bold; }

.post-section { margin-bottom: 18px; }
.section-label {
  font-size: 0.75rem;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #888;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.copy-btn {
  padding: 2px 8px;
  border: 1px solid #ddd;
  background: #fff;
  font-family: inherit;
  font-size: 0.72rem;
  cursor: pointer;
  transition: background 0.1s;
}
.copy-btn:hover { background: #f0f0f0; }
.copy-btn.copied { background: #e8f8e8; border-color: #090; color: #090; }

.post-copy   { line-height: 1.7; white-space: pre-wrap; font-size: 0.92rem; }
.hashtag-line { color: #0077b5; font-size: 0.88rem; word-break: break-word; }
.cta-text    { font-weight: bold; font-size: 0.92rem; }
.visual-text { font-style: italic; color: #666; font-size: 0.88rem; }

.revision-note {
  background: #fff8e0;
  border: 1px solid #f0c040;
  padding: 12px 16px;
  font-size: 0.85rem;
  margin-bottom: 18px;
  line-height: 1.5;
}

.post-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}

.btn-primary {
  padding: 10px 20px;
  background: #111;
  color: #fff;
  border: 2px solid #111;
  font-family: inherit;
  font-size: 0.88rem;
  cursor: pointer;
  font-weight: bold;
}
.btn-primary:hover { background: #333; }
.btn-outline {
  padding: 10px 20px;
  background: transparent;
  color: #090;
  border: 2px solid #090;
  font-family: inherit;
  font-size: 0.88rem;
  cursor: pointer;
}
.btn-ghost {
  padding: 10px 20px;
  background: transparent;
  color: #111;
  border: 2px solid #ddd;
  font-family: inherit;
  font-size: 0.88rem;
  cursor: pointer;
}
</style>
