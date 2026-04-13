<template>
  <div class="agency-content">
    <nav class="agency-nav">
      <router-link to="/agency/portal" class="nav-back">← Back to Portal</router-link>
      <div class="nav-title">{{ package_?.month_label || '' }} Content Package</div>
      <button class="btn-outline-sm" @click="downloadPackage">Download JSON</button>
    </nav>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading content…</p>
    </div>

    <template v-else-if="package_">
      <div class="content-inner">
        <!-- Platform filter tabs -->
        <div class="platform-tabs">
          <button v-for="p in tabs" :key="p"
                  :class="['tab', { active: activeTab === p }]"
                  @click="activeTab = p">
            {{ p === 'all' ? 'All Platforms' : p }}
            <span class="tab-count">{{ postCountFor(p) }}</span>
          </button>
        </div>

        <!-- Stats bar -->
        <div class="stats-bar">
          <div class="stat">
            <span class="stat-val">{{ filteredPosts.length }}</span>
            <span class="stat-label">Posts shown</span>
          </div>
          <div class="stat">
            <span class="stat-val">{{ approvedCount }}</span>
            <span class="stat-label">Approved</span>
          </div>
          <div class="stat">
            <span class="stat-val">{{ revisionCount }}</span>
            <span class="stat-label">Revision requested</span>
          </div>
        </div>

        <!-- Content calendar / grid -->
        <ContentCalendar
          :posts="filteredPosts"
          @select-post="openPost"
        />
      </div>
    </template>

    <div v-else class="error-state">
      <p>Content package not found.</p>
      <router-link to="/agency/portal" class="btn-primary">Back to Portal</router-link>
    </div>

    <!-- Post detail modal -->
    <div v-if="selectedPost" class="modal-overlay" @click.self="selectedPost = null">
      <div class="modal post-modal">
        <button class="modal-close" @click="selectedPost = null">×</button>
        <PostCard
          :post="selectedPost"
          @request-revision="openRevisionForm"
          @approve="approvePost"
        />
      </div>
    </div>

    <!-- Revision form -->
    <div v-if="revisionPost" class="modal-overlay" @click.self="revisionPost = null">
      <div class="modal">
        <button class="modal-close" @click="revisionPost = null">×</button>
        <h3>Request Revision</h3>
        <p class="revision-hint">Tell us what to change about day {{ revisionPost.day_number }} on {{ revisionPost.platform }}.</p>
        <textarea v-model="revisionNote" rows="5" placeholder="e.g. Make it more casual, remove the price mention, focus on the community aspect…" class="revision-textarea"></textarea>
        <button class="btn-primary" @click="submitRevision" :disabled="savingRevision">
          {{ savingRevision ? 'Saving…' : 'Submit Revision Request' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import ContentCalendar from '../../components/agency/ContentCalendar.vue'
import PostCard from '../../components/agency/PostCard.vue'
import { getContentPackage, updatePost, downloadContentPackage } from '../../api/agency.js'

const props = defineProps({ id: String })
const route = useRoute()
const pkgId = props.id || route.params.id

const loading     = ref(true)
const package_    = ref(null)
const activeTab   = ref('all')
const selectedPost = ref(null)
const revisionPost = ref(null)
const revisionNote = ref('')
const savingRevision = ref(false)

const tabs = computed(() => {
  if (!package_.value) return ['all']
  return ['all', ...(package_.value.platforms || [])]
})

const filteredPosts = computed(() => {
  if (!package_.value?.posts) return []
  if (activeTab.value === 'all') return package_.value.posts
  return package_.value.posts.filter(p => p.platform === activeTab.value)
})

const approvedCount  = computed(() => (package_.value?.posts || []).filter(p => p.is_approved).length)
const revisionCount  = computed(() => (package_.value?.posts || []).filter(p => p.revision_note).length)

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
.agency-content { font-family: 'Courier New', monospace; background: #f9f9f9; min-height: 100vh; }
.agency-nav { display: flex; justify-content: space-between; align-items: center; padding: 16px 40px; border-bottom: 2px solid #111; background: #fff; position: sticky; top: 0; z-index: 100; }
.nav-back { color: #111; text-decoration: none; font-size: 0.9rem; }
.nav-title { font-weight: bold; }
.btn-outline-sm { background: transparent; border: 2px solid #111; padding: 8px 16px; font-family: inherit; font-size: 0.85rem; cursor: pointer; }
.btn-outline-sm:hover { background: #f0f0f0; }

.content-inner { max-width: 1200px; margin: 0 auto; padding: 32px 24px; }

.platform-tabs { display: flex; gap: 0; border-bottom: 2px solid #111; margin-bottom: 24px; flex-wrap: wrap; }
.tab { padding: 12px 24px; background: transparent; border: none; border-bottom: 4px solid transparent; cursor: pointer; font-family: inherit; font-size: 0.9rem; margin-bottom: -2px; color: #888; }
.tab.active { border-bottom-color: #111; color: #111; font-weight: bold; }
.tab:hover { color: #111; }
.tab-count { margin-left: 6px; background: #f0f0f0; padding: 1px 6px; font-size: 0.75rem; border-radius: 10px; }

.stats-bar { display: flex; gap: 32px; margin-bottom: 32px; padding: 16px 0; border-bottom: 1px solid #eee; }
.stat { text-align: center; }
.stat-val { display: block; font-size: 1.6rem; font-weight: bold; }
.stat-label { font-size: 0.78rem; color: #888; }

.loading-state { text-align: center; padding: 80px 0; }
.spinner { width: 40px; height: 40px; border: 3px solid #eee; border-top-color: #111; border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 16px; }
@keyframes spin { to { transform: rotate(360deg); } }
.error-state { text-align: center; padding: 80px 0; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 24px; }
.modal { background: #fff; border: 2px solid #111; padding: 36px; width: 100%; max-width: 580px; position: relative; max-height: 90vh; overflow-y: auto; }
.post-modal { max-width: 680px; }
.modal h3 { font-size: 1.3rem; margin-bottom: 12px; }
.modal-close { position: absolute; top: 16px; right: 16px; background: none; border: none; font-size: 1.5rem; cursor: pointer; }
.revision-hint { color: #555; font-size: 0.9rem; margin-bottom: 16px; }
.revision-textarea { width: 100%; padding: 12px; border: 2px solid #ccc; font-family: inherit; font-size: 0.9rem; box-sizing: border-box; resize: vertical; margin-bottom: 16px; }
.btn-primary { display: inline-block; background: #111; color: #fff; padding: 12px 24px; font-family: inherit; font-size: 0.9rem; font-weight: bold; border: 2px solid #111; cursor: pointer; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
