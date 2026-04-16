<template>
  <div ref="root" class="cagency content-view">
    <a href="#main" class="ca-skip">Skip to content</a>

    <nav class="ca-nav" aria-label="Package">
      <router-link to="/agency/portal" class="nav-back">
        <span aria-hidden="true">←</span> Back to portal
      </router-link>
      <div class="nav-title">{{ package_?.month_label || '' }}</div>
      <button
        class="ca-btn secondary sm"
        @click="downloadPackage"
        :disabled="!package_"
      >Download JSON</button>
    </nav>

    <main id="main" class="inner">
      <div v-if="loading" class="state" role="status" aria-live="polite">
        <span class="spinner" aria-hidden="true"></span>
        <p>Loading content…</p>
      </div>

      <template v-else-if="package_">
        <header class="head reveal">
          <span class="ca-kicker">Content calendar</span>
          <h1>{{ package_.month_label }} package</h1>
          <p class="sub">
            {{ package_.post_count }} posts across
            {{ (package_.platforms || []).join(', ') }}.
          </p>
        </header>

        <div class="tabs reveal" role="tablist">
          <button
            v-for="p in tabs"
            :key="p"
            :class="['tab', { active: activeTab === p }]"
            role="tab"
            :aria-selected="activeTab === p"
            @click="activeTab = p"
          >
            <span>{{ p === 'all' ? 'All' : p }}</span>
            <span class="tab-count">{{ postCountFor(p) }}</span>
          </button>
        </div>

        <div class="stats reveal">
          <div class="stat">
            <span class="stat-num">{{ filteredPosts.length }}</span>
            <span class="stat-lbl">Posts shown</span>
          </div>
          <div class="stat">
            <span class="stat-num">{{ approvedCount }}</span>
            <span class="stat-lbl">Approved</span>
          </div>
          <div class="stat">
            <span class="stat-num">{{ revisionCount }}</span>
            <span class="stat-lbl">Revision requested</span>
          </div>
        </div>

        <section class="cal-section reveal">
          <ContentCalendar :posts="filteredPosts" @select-post="openPost" />
        </section>
      </template>

      <div v-else class="state error">
        <p>Content package not found.</p>
        <router-link to="/agency/portal" class="ca-btn">Back to portal</router-link>
      </div>
    </main>

    <Transition name="fade">
      <div
        v-if="selectedPost"
        class="overlay"
        role="dialog"
        aria-modal="true"
        aria-labelledby="post-modal-title"
        @click.self="selectedPost = null"
        @keydown.esc="selectedPost = null"
      >
        <div class="modal post-modal ca-card">
          <button class="modal-close" @click="selectedPost = null" aria-label="Close">×</button>
          <h2 id="post-modal-title" class="visually-hidden">Post detail</h2>
          <PostCard
            :post="selectedPost"
            @request-revision="openRevisionForm"
            @approve="approvePost"
          />
        </div>
      </div>
    </Transition>

    <Transition name="fade">
      <div
        v-if="revisionPost"
        class="overlay"
        role="dialog"
        aria-modal="true"
        aria-labelledby="rev-title"
        @click.self="revisionPost = null"
        @keydown.esc="revisionPost = null"
      >
        <div class="modal ca-card">
          <button class="modal-close" @click="revisionPost = null" aria-label="Close">×</button>
          <span class="ca-kicker">Revise</span>
          <h3 id="rev-title">Request revision</h3>
          <p class="rev-hint">
            Tell us what to change about day {{ revisionPost.day_number }}
            on {{ revisionPost.platform }}.
          </p>
          <div class="ca-field">
            <label for="rev-note">Revision notes</label>
            <textarea
              id="rev-note"
              v-model="revisionNote"
              rows="5"
              placeholder="e.g. Make it more casual, remove the price mention, focus on the community aspect…"
            ></textarea>
          </div>
          <button
            class="ca-btn"
            @click="submitRevision"
            :disabled="savingRevision || !revisionNote.trim()"
          >{{ savingRevision ? 'Saving…' : 'Submit revision request' }}</button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import ContentCalendar from '../../components/agency/ContentCalendar.vue'
import PostCard from '../../components/agency/PostCard.vue'
import { getContentPackage, updatePost, downloadContentPackage } from '../../api/agency.js'
import { useReveal } from '../../composables/useReveal.js'

const props = defineProps({ id: String })
const route = useRoute()
const pkgId = props.id || route.params.id

const root        = ref(null)
const loading     = ref(true)
const package_    = ref(null)
const activeTab   = ref('all')
const selectedPost = ref(null)
const revisionPost = ref(null)
const revisionNote = ref('')
const savingRevision = ref(false)

useReveal(root)

const tabs = computed(() => {
  if (!package_.value) return ['all']
  return ['all', ...(package_.value.platforms || [])]
})

const filteredPosts = computed(() => {
  if (!package_.value?.posts) return []
  if (activeTab.value === 'all') return package_.value.posts
  return package_.value.posts.filter(p => p.platform === activeTab.value)
})

const approvedCount = computed(() => (package_.value?.posts || []).filter(p => p.is_approved).length)
const revisionCount = computed(() => (package_.value?.posts || []).filter(p => p.revision_note).length)

function postCountFor(tab) {
  if (!package_.value?.posts) return 0
  if (tab === 'all') return package_.value.posts.length
  return package_.value.posts.filter(p => p.platform === tab).length
}

function openPost(post) { selectedPost.value = post }

function openRevisionForm(post) {
  revisionPost.value = post
  revisionNote.value = post.revision_note || ''
  selectedPost.value = null
}

async function approvePost(post) {
  try {
    const res = await updatePost(pkgId, post.id, { is_approved: true })
    const idx = package_.value.posts.findIndex(p => p.id === post.id)
    if (idx !== -1) package_.value.posts[idx] = res.data
    selectedPost.value = null
  } catch { /* ignore */ }
}

async function submitRevision() {
  if (!revisionNote.value.trim()) return
  savingRevision.value = true
  try {
    const res = await updatePost(pkgId, revisionPost.value.id, { revision_note: revisionNote.value })
    const idx = package_.value.posts.findIndex(p => p.id === revisionPost.value.id)
    if (idx !== -1) package_.value.posts[idx] = res.data
    revisionPost.value = null
    revisionNote.value = ''
  } catch { /* ignore */ } finally {
    savingRevision.value = false
  }
}

async function downloadPackage() {
  try {
    const res = await downloadContentPackage(pkgId)
    const blob = new Blob([JSON.stringify(res, null, 2)], { type: 'application/json' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href = url
    a.download = `content-package-${pkgId.slice(0, 8)}.json`
    a.click()
    URL.revokeObjectURL(url)
  } catch { /* ignore */ }
}

onMounted(async () => {
  try {
    const res = await getContentPackage(pkgId)
    package_.value = res.data
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.ca-nav { gap: var(--s-4); }
.nav-back {
  font-size: var(--small);
  color: var(--ink-mid);
  text-decoration: none;
  display: inline-flex; align-items: center; gap: 6px;
  transition: color var(--dur-2) var(--ease-out);
}
.nav-back:hover { color: var(--ink-hi); }
.nav-title {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 1rem;
  letter-spacing: -0.015em;
  color: var(--ink-hi);
}

.inner {
  max-width: var(--page);
  margin: 0 auto;
  padding: var(--s-8) var(--s-5) var(--s-10);
}

.head { margin-bottom: var(--s-7); }
.head h1 { font-size: var(--display-3); margin: var(--s-2) 0 var(--s-3); }
.head .sub { color: var(--ink-mid); font-size: var(--body-lg); }

.tabs {
  display: flex; gap: var(--s-2);
  border-bottom: 1px solid var(--hairline);
  margin-bottom: var(--s-6);
  flex-wrap: wrap;
}
.tab {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 18px;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  font: inherit;
  font-size: var(--small);
  color: var(--ink-lo);
  text-transform: capitalize;
  margin-bottom: -1px;
  transition: color var(--dur-2) var(--ease-out),
              border-color var(--dur-2) var(--ease-out);
}
.tab:hover { color: var(--ink-hi); }
.tab.active {
  color: var(--ink-hi);
  border-bottom-color: var(--ink-hi);
  font-weight: 500;
}
.tab:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; border-radius: var(--r-1); }
.tab-count {
  font-family: var(--font-mono);
  font-size: var(--mono-cap);
  padding: 1px 8px;
  border-radius: var(--r-full);
  background: var(--surface-2);
  color: var(--ink-lo);
}
.tab.active .tab-count { background: var(--ink-hi); color: var(--paper); }

.stats {
  display: flex; gap: var(--s-7);
  padding: var(--s-5) 0;
  border-bottom: 1px solid var(--hairline);
  margin-bottom: var(--s-6);
  flex-wrap: wrap;
}
.stat { display: flex; flex-direction: column; gap: 4px; }
.stat-num {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 2rem;
  letter-spacing: -0.025em;
  color: var(--ink-hi);
  font-variant-numeric: tabular-nums;
}
.stat-lbl {
  font-family: var(--font-mono);
  font-size: var(--mono-cap);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--ink-lo);
}

.cal-section { margin-top: var(--s-5); }

.state {
  display: flex; flex-direction: column; align-items: center; gap: var(--s-4);
  padding: var(--s-10) 0;
  color: var(--ink-mid);
}
.spinner {
  width: 26px; height: 26px;
  border: 2px solid color-mix(in oklab, var(--ink-hi), transparent 88%);
  border-top-color: var(--ink-hi);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.overlay {
  position: fixed; inset: 0;
  background: color-mix(in oklab, var(--void), transparent 45%);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  display: flex; align-items: center; justify-content: center;
  padding: var(--s-5);
  z-index: 1000;
}
.modal {
  position: relative;
  width: 100%; max-width: 580px;
  max-height: 92vh;
  overflow-y: auto;
  padding: var(--s-7);
  background: var(--paper);
  box-shadow: var(--shadow-lg);
}
.post-modal { max-width: 720px; }
.modal h3 { font-size: 1.5rem; margin: var(--s-2) 0 var(--s-4); }
.modal-close {
  position: absolute; top: 12px; right: 12px;
  width: 36px; height: 36px;
  background: transparent; border: none;
  color: var(--ink-mid); cursor: pointer;
  font-size: 1.6rem; line-height: 1;
  border-radius: var(--r-full);
  transition: background var(--dur-2) var(--ease-out);
}
.modal-close:hover { background: var(--surface-2); }
.modal-close:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }
.rev-hint { color: var(--ink-mid); font-size: var(--small); margin: 0 0 var(--s-4); }

.visually-hidden {
  position: absolute !important;
  width: 1px; height: 1px;
  padding: 0; margin: -1px; overflow: hidden;
  clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity var(--dur-3) var(--ease-out);
}
.fade-enter-active .modal, .fade-leave-active .modal {
  transition: transform var(--dur-3) var(--ease-out),
              opacity   var(--dur-3) var(--ease-out);
}
.fade-enter-from, .fade-leave-to { opacity: 0; }
.fade-enter-from .modal, .fade-leave-to .modal {
  opacity: 0;
  transform: translateY(12px) scale(0.985);
}
</style>
