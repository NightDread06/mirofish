<template>
  <div class="post-card">
    <header class="pc-head">
      <div class="pc-meta">
        <span class="plat-badge" :class="post.platform">
          {{ platformLabel(post.platform) }}
        </span>
        <span class="ca-pill type-pill">{{ post.post_type }}</span>
        <span class="pc-day">Day {{ post.day_number }}</span>
        <span class="pc-date">{{ formatDate(post.scheduled_date) }}</span>
      </div>
      <div class="pc-status">
        <span v-if="post.is_approved" class="ca-pill ok">✓ Approved</span>
        <span v-else-if="post.revision_note" class="ca-pill warn">Revision requested</span>
      </div>
    </header>

    <section class="pc-section">
      <div class="pc-label">
        <span class="ca-kicker">Post copy</span>
        <button
          class="copy-btn"
          @click="copyText(post.post_copy, 'copy')"
          :class="{ copied: copiedField === 'copy' }"
          :aria-label="copiedField === 'copy' ? 'Copied' : 'Copy post copy'"
        >{{ copiedField === 'copy' ? 'Copied' : 'Copy' }}</button>
      </div>
      <p class="pc-copy">{{ post.post_copy }}</p>
    </section>

    <section v-if="post.hashtags" class="pc-section">
      <div class="pc-label">
        <span class="ca-kicker">Hashtags</span>
        <button
          class="copy-btn"
          @click="copyText(post.hashtags, 'hashtags')"
          :class="{ copied: copiedField === 'hashtags' }"
          :aria-label="copiedField === 'hashtags' ? 'Copied' : 'Copy hashtags'"
        >{{ copiedField === 'hashtags' ? 'Copied' : 'Copy' }}</button>
      </div>
      <p class="pc-hash">{{ post.hashtags }}</p>
    </section>

    <section v-if="post.call_to_action" class="pc-section">
      <span class="ca-kicker">Call to action</span>
      <p class="pc-cta">{{ post.call_to_action }}</p>
    </section>

    <section v-if="post.visual_description" class="pc-section">
      <span class="ca-kicker">Visual direction</span>
      <p class="pc-visual">{{ post.visual_description }}</p>
    </section>

    <aside v-if="post.revision_note" class="pc-revnote">
      <strong>Revision note</strong>
      <p>{{ post.revision_note }}</p>
    </aside>

    <footer class="pc-actions">
      <button class="ca-btn" @click="copyAll">
        {{ copiedField === 'all' ? 'Copied all text' : 'Copy all text' }}
      </button>
      <button v-if="!post.is_approved" class="ca-btn secondary" @click="$emit('approve', post)">
        Mark approved
      </button>
      <button class="ca-btn ghost" @click="$emit('request-revision', post)">
        Request revision
      </button>
    </footer>
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
.post-card {
  font-family: var(--font-body);
  color: var(--ink);
}

.pc-head {
  display: flex; justify-content: space-between; align-items: flex-start;
  gap: var(--s-3); flex-wrap: wrap;
  margin-bottom: var(--s-5);
  padding-bottom: var(--s-4);
  border-bottom: 1px solid var(--hairline);
}
.pc-meta { display: flex; flex-wrap: wrap; gap: var(--s-2); align-items: center; }

.plat-badge {
  font-family: var(--font-mono);
  font-size: var(--mono-cap);
  letter-spacing: 0.06em;
  padding: 4px 10px;
  border-radius: var(--r-full);
  border: 1px solid;
  text-transform: none;
}
.plat-badge.linkedin  { color: oklch(0.40 0.13 245); border-color: color-mix(in oklab, oklch(0.40 0.13 245), transparent 55%); background: color-mix(in oklab, oklch(0.40 0.13 245), var(--paper) 88%); }
.plat-badge.instagram { color: oklch(0.50 0.18 350); border-color: color-mix(in oklab, oklch(0.50 0.18 350), transparent 55%); background: color-mix(in oklab, oklch(0.50 0.18 350), var(--paper) 88%); }
.plat-badge.facebook  { color: oklch(0.42 0.15 260); border-color: color-mix(in oklab, oklch(0.42 0.15 260), transparent 55%); background: color-mix(in oklab, oklch(0.42 0.15 260), var(--paper) 88%); }
.plat-badge.twitter   { color: var(--ink-hi); border-color: var(--hairline-2); background: var(--surface-2); }

.type-pill { text-transform: capitalize; }
.pc-day  {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 0.9rem;
  letter-spacing: -0.01em;
}
.pc-date { font-size: var(--caption); color: var(--ink-lo); font-family: var(--font-mono); letter-spacing: 0.03em; }

.pc-section { margin-bottom: var(--s-5); }
.pc-label {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: var(--s-2);
  gap: var(--s-2);
}
.copy-btn {
  font-family: var(--font-mono);
  font-size: var(--mono-cap);
  letter-spacing: 0.06em;
  padding: 4px 10px;
  border: 1px solid var(--hairline);
  background: var(--paper);
  color: var(--ink-mid);
  cursor: pointer;
  border-radius: var(--r-full);
  transition: all var(--dur-2) var(--ease-out);
}
.copy-btn:hover { border-color: var(--ink-hi); color: var(--ink-hi); }
.copy-btn.copied {
  background: color-mix(in oklab, var(--ok), var(--paper) 88%);
  border-color: color-mix(in oklab, var(--ok), transparent 60%);
  color: var(--ok);
}
.copy-btn:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }

.pc-copy {
  font-size: 1.0625rem;
  line-height: 1.65;
  white-space: pre-wrap;
  color: var(--ink-hi);
  max-width: 62ch;
}
.pc-hash {
  font-family: var(--font-mono);
  font-size: var(--small);
  color: var(--brand);
  word-break: break-word;
  line-height: 1.7;
}
.pc-cta {
  font-family: var(--font-display);
  font-weight: 600;
  font-style: italic;
  font-size: 1.0625rem;
  color: var(--ink-hi);
}
.pc-visual {
  font-style: italic;
  color: var(--ink-mid);
  font-size: var(--small);
  line-height: 1.6;
}

.pc-revnote {
  background: var(--flame-wash);
  border: 1px solid color-mix(in oklab, var(--flame), transparent 70%);
  border-radius: var(--r-3);
  padding: var(--s-4) var(--s-5);
  margin-bottom: var(--s-5);
}
.pc-revnote strong {
  display: block;
  font-family: var(--font-mono);
  font-size: var(--mono-cap);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: oklch(0.45 0.15 75);
  margin-bottom: var(--s-2);
}
.pc-revnote p { margin: 0; color: var(--ink); font-size: var(--small); line-height: 1.6; }

.pc-actions {
  display: flex; flex-wrap: wrap; gap: var(--s-2);
  margin-top: var(--s-6);
  padding-top: var(--s-5);
  border-top: 1px solid var(--hairline);
}
</style>
