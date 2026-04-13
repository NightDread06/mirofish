<template>
  <div class="agency-portal">
    <nav class="agency-nav">
      <router-link to="/agency" class="nav-brand">ContentAgency.ai</router-link>
      <div class="nav-links">
        <router-link v-if="auth.state.isAdmin" to="/agency/admin">Admin</router-link>
        <button class="btn-ghost-sm" @click="handleLogout">Log Out</button>
      </div>
    </nav>

    <div class="portal-inner">
      <!-- Loading -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Loading your portal…</p>
      </div>

      <!-- No profile yet -->
      <div v-else-if="!client" class="empty-state">
        <h2>Welcome! Let's set up your profile.</h2>
        <p>Complete a quick 3-minute form and we'll generate your first 30-day content calendar.</p>
        <router-link to="/agency/onboarding" class="btn-primary">Complete Onboarding →</router-link>
      </div>

      <!-- Portal content -->
      <template v-else>
        <div class="portal-header">
          <div>
            <h1>{{ client.business_name }}</h1>
            <span class="status-badge" :class="client.status">{{ client.status }}</span>
            <span class="plan-badge" :class="client.plan">{{ client.plan }}</span>
          </div>
          <button class="btn-primary" @click="showGenerateModal = true">
            + Generate New Package
          </button>
        </div>

        <!-- Content packages -->
        <section class="packages-section">
          <h2>Content Packages</h2>
          <div v-if="packages.length === 0" class="empty-packages">
            <p>No content packages yet. Generate your first 30-day calendar above.</p>
          </div>
          <div v-else class="packages-grid">
            <div v-for="pkg in packages" :key="pkg.id" class="package-card"
                 :class="pkg.status" @click="openPackage(pkg)">
              <div class="pkg-header">
                <span class="pkg-month">{{ pkg.month_label }}</span>
                <span class="pkg-status-badge" :class="pkg.status">{{ pkg.status }}</span>
              </div>
              <div class="pkg-platforms">
                <span v-for="p in (pkg.platforms || [])" :key="p" class="platform-tag">{{ p }}</span>
              </div>
              <div class="pkg-meta">
                <span>{{ pkg.post_count }} posts</span>
                <span>{{ pkg.model_used?.includes('sonnet') ? 'Premium' : 'Standard' }}</span>
              </div>
              <!-- Progress bar for generating packages -->
              <div v-if="pkg.status === 'generating' || pkg.status === 'pending'" class="progress-bar">
                <div class="progress-fill" :style="{ width: (pkg.progress || 5) + '%' }"></div>
              </div>
              <p v-if="pkg.status === 'generating' || pkg.status === 'pending'"
                 class="progress-msg">{{ pkg.progress_message || 'Generating…' }}</p>
            </div>
          </div>
        </section>

        <!-- Quick tips -->
        <section class="tips-section">
          <h2>Getting the most from your content</h2>
          <div class="tips-grid">
            <div class="tip">
              <strong>Best posting times:</strong> LinkedIn Tue–Thu 8–10am · Instagram Wed–Fri 11am–1pm · Facebook Tue–Thu 9am
            </div>
            <div class="tip">
              <strong>Hashtag tip:</strong> Mix 3 niche tags + 3 location tags + 3 broad community tags per post.
            </div>
            <div class="tip">
              <strong>Visual tip:</strong> Use the visual description as a brief for your photographer or to search Unsplash.
            </div>
          </div>
        </section>
      </template>
    </div>

    <!-- Generate modal -->
    <div v-if="showGenerateModal" class="modal-overlay" @click.self="showGenerateModal = false">
      <div class="modal">
        <button class="modal-close" @click="showGenerateModal = false">×</button>
        <h3>Generate 30-Day Content Package</h3>
        <div class="form-group">
          <label>Start date</label>
          <input v-model="genForm.start_date" type="date" />
        </div>
        <div class="form-group">
          <label>Platforms</label>
          <div class="platform-checkboxes">
            <label v-for="p in allPlatforms" :key="p" class="checkbox-label-inline">
              <input type="checkbox" :value="p" v-model="genForm.platforms" />
              {{ p }}
            </label>
          </div>
        </div>
        <p v-if="genError" class="form-error">{{ genError }}</p>
        <button class="btn-primary" @click="generateContent" :disabled="generating">
          {{ generating ? 'Submitting…' : 'Generate Package →' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAgencyAuth } from '../../store/agencyAuth.js'
import { getMyProfile, getClientPackages, generateContent as apiGenerateContent } from '../../api/agency.js'

const router = useRouter()
const auth   = useAgencyAuth()

const loading = ref(true)
const client  = ref(null)
const packages = ref([])

const showGenerateModal = ref(false)
const generating = ref(false)
const genError   = ref('')
const allPlatforms = ['linkedin', 'instagram', 'facebook', 'twitter']

const genForm = ref({
  start_date: new Date().toISOString().slice(0, 10),
  platforms: ['linkedin', 'instagram', 'facebook'],
})

let pollInterval = null

async function loadPortal() {
  try {
    const res = await getMyProfile()
    client.value = res.data
    await loadPackages()
  } catch {
    client.value = null
  } finally {
    loading.value = false
  }
}

async function loadPackages() {
  if (!client.value) return
  try {
    const res = await getClientPackages(client.value.id)
    packages.value = res.data || []
  } catch { /* ignore */ }
}

async function pollGeneratingPackages() {
  const inFlight = packages.value.filter(
    p => p.status === 'pending' || p.status === 'generating'
  )
  if (inFlight.length === 0) return

  const { getContentPackage } = await import('../../api/agency.js')
  for (const pkg of inFlight) {
    try {
      const res = await getContentPackage(pkg.id)
      const idx = packages.value.findIndex(p => p.id === pkg.id)
      if (idx !== -1) packages.value[idx] = res.data
    } catch { /* ignore */ }
  }
}

async function generateContent() {
  genError.value  = ''
  generating.value = true
  try {
    await apiGenerateContent({
      client_id:  client.value.id,
      start_date: genForm.value.start_date,
      platforms:  genForm.value.platforms,
    })
    showGenerateModal.value = false
    await loadPackages()
  } catch (err) {
    genError.value = err?.message || 'Failed to start generation'
  } finally {
    generating.value = false
  }
}

function openPackage(pkg) {
  if (pkg.status === 'completed') {
    router.push(`/agency/portal/content/${pkg.id}`)
  }
}

async function handleLogout() {
  await auth.logout()
  router.push('/agency')
}

onMounted(async () => {
  await loadPortal()
  // Poll in-flight packages every 3 seconds
  pollInterval = setInterval(pollGeneratingPackages, 3000)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})
</script>

<style scoped>
.agency-portal { font-family: 'Courier New', monospace; background: #f9f9f9; min-height: 100vh; }
.agency-nav { display: flex; justify-content: space-between; align-items: center; padding: 20px 40px; border-bottom: 2px solid #111; background: #fff; position: sticky; top: 0; z-index: 100; }
.nav-brand { font-size: 1.2rem; font-weight: bold; text-decoration: none; color: #111; }
.nav-links { display: flex; align-items: center; gap: 16px; }
.nav-links a { color: #111; text-decoration: none; font-size: 0.9rem; }

.portal-inner { max-width: 1000px; margin: 0 auto; padding: 48px 24px; }

.loading-state { text-align: center; padding: 80px 0; }
.spinner { width: 40px; height: 40px; border: 3px solid #eee; border-top-color: #111; border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 16px; }
@keyframes spin { to { transform: rotate(360deg); } }

.empty-state { text-align: center; padding: 80px 0; border: 2px dashed #ddd; background: #fff; }
.empty-state h2 { margin-bottom: 12px; }
.empty-state p { color: #555; margin-bottom: 28px; }

.portal-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 40px; flex-wrap: wrap; gap: 16px; }
.portal-header h1 { font-size: 2rem; margin-bottom: 8px; }
.status-badge, .plan-badge { display: inline-block; padding: 3px 10px; font-size: 0.78rem; border: 1px solid; margin-right: 8px; text-transform: uppercase; letter-spacing: 0.05em; }
.status-badge.active { border-color: #090; color: #090; }
.status-badge.onboarding { border-color: #f90; color: #f90; }
.plan-badge.pilot { border-color: #999; color: #999; }
.plan-badge.retainer { border-color: #09f; color: #09f; }

.packages-section { margin-bottom: 48px; }
.packages-section h2 { font-size: 1.4rem; margin-bottom: 24px; }
.empty-packages { padding: 32px; border: 2px dashed #ddd; text-align: center; color: #888; background: #fff; }

.packages-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 20px; }
.package-card { background: #fff; border: 2px solid #ddd; padding: 24px; cursor: pointer; transition: border-color 0.15s; }
.package-card.completed { cursor: pointer; }
.package-card.completed:hover { border-color: #111; }
.pkg-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.pkg-month { font-weight: bold; font-size: 1rem; }
.pkg-status-badge { padding: 2px 8px; font-size: 0.75rem; border: 1px solid; }
.pkg-status-badge.completed { border-color: #090; color: #090; }
.pkg-status-badge.pending, .pkg-status-badge.generating { border-color: #f90; color: #f90; }
.pkg-status-badge.failed { border-color: #c00; color: #c00; }
.pkg-platforms { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
.platform-tag { background: #f0f0f0; padding: 2px 8px; font-size: 0.75rem; }
.pkg-meta { display: flex; justify-content: space-between; font-size: 0.82rem; color: #888; }
.progress-bar { height: 4px; background: #eee; margin-top: 12px; }
.progress-fill { height: 100%; background: #111; transition: width 0.5s; }
.progress-msg { font-size: 0.78rem; color: #888; margin-top: 8px; }

.tips-section h2 { font-size: 1.4rem; margin-bottom: 20px; }
.tips-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; }
.tip { background: #fff; border: 1px solid #eee; padding: 20px; font-size: 0.88rem; line-height: 1.6; }

.btn-primary { display: inline-block; background: #111; color: #fff; padding: 12px 24px; font-family: inherit; font-size: 0.9rem; font-weight: bold; border: 2px solid #111; cursor: pointer; text-decoration: none; }
.btn-primary:hover:not(:disabled) { background: #333; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-ghost-sm { background: transparent; border: 1px solid #ddd; padding: 8px 16px; font-family: inherit; font-size: 0.85rem; cursor: pointer; }
.btn-ghost-sm:hover { background: #f0f0f0; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal { background: #fff; border: 2px solid #111; padding: 40px; width: 100%; max-width: 460px; position: relative; }
.modal h3 { font-size: 1.4rem; margin-bottom: 24px; }
.modal-close { position: absolute; top: 16px; right: 16px; background: none; border: none; font-size: 1.5rem; cursor: pointer; }
.form-group { margin-bottom: 20px; }
.form-group label { display: block; font-size: 0.85rem; font-weight: bold; margin-bottom: 6px; }
.form-group input { width: 100%; padding: 10px; border: 2px solid #ccc; font-family: inherit; font-size: 0.95rem; box-sizing: border-box; }
.platform-checkboxes { display: flex; flex-wrap: wrap; gap: 12px; }
.checkbox-label-inline { display: flex; align-items: center; gap: 6px; font-size: 0.9rem; cursor: pointer; }
.form-error { color: #c00; font-size: 0.85rem; margin-bottom: 12px; }
</style>
