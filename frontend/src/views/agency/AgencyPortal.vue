<template>
  <div ref="root" class="cagency portal">
    <a href="#main" class="ca-skip">Skip to content</a>

    <nav class="ca-nav" aria-label="Portal">
      <router-link to="/agency" class="ca-brand">
        <span class="dot" aria-hidden="true"></span>ContentAgency
      </router-link>
      <div class="ca-nav-links">
        <router-link v-if="auth.state.isAdmin" to="/agency/admin">Admin</router-link>
        <button class="ca-btn ghost sm" @click="handleLogout">Log out</button>
      </div>
    </nav>

    <main id="main" class="portal-inner">
      <div v-if="loading" class="state" role="status" aria-live="polite">
        <span class="spinner" aria-hidden="true"></span>
        <p>Loading your portal…</p>
      </div>

      <section v-else-if="!client" class="empty reveal">
        <span class="ca-kicker">Welcome</span>
        <h1>Let's set up your studio.</h1>
        <p class="lede">
          A three-minute conversation about your business, then we generate
          your first 30-day calendar.
        </p>
        <router-link to="/agency/onboarding" class="ca-btn lg">
          Start onboarding →
        </router-link>
      </section>

      <template v-else>
        <header class="portal-head reveal">
          <div class="head-text">
            <span class="ca-kicker">Studio</span>
            <h1>{{ client.business_name }}</h1>
            <div class="head-pills">
              <span class="ca-pill" :class="statusPill(client.status)">
                {{ client.status }}
              </span>
              <span class="ca-pill" :class="planPill(client.plan)">
                {{ client.plan }}
              </span>
            </div>
          </div>
          <button class="ca-btn" @click="openGenerate">
            Generate new package
          </button>
        </header>

        <hr class="ca-hair" />

        <section class="packages reveal" aria-labelledby="pkgs-h">
          <div class="section-head">
            <h2 id="pkgs-h">Content packages</h2>
            <span class="count-mono">{{ packages.length }} total</span>
          </div>

          <div v-if="packages.length === 0" class="empty-soft">
            <p>No packages yet. Generate your first 30-day calendar above.</p>
          </div>

          <div v-else class="pkg-grid">
            <article
              v-for="pkg in packages"
              :key="pkg.id"
              class="pkg-card ca-card"
              :class="[pkg.status, { hoverable: pkg.status === 'completed' }]"
              :aria-busy="pkg.status === 'generating' || pkg.status === 'pending'"
              tabindex="0"
              @click="openPackage(pkg)"
              @keydown.enter="openPackage(pkg)"
            >
              <div class="pkg-top">
                <span class="pkg-month">{{ pkg.month_label }}</span>
                <span class="ca-pill" :class="statusPill(pkg.status)">
                  {{ pkg.status }}
                </span>
              </div>

              <div class="pkg-platforms">
                <span
                  v-for="p in pkg.platforms || []"
                  :key="p"
                  class="plat-tag"
                >{{ p }}</span>
              </div>

              <div class="pkg-meta">
                <span>{{ pkg.post_count }} posts</span>
                <span class="mono">
                  {{ pkg.model_used?.includes('sonnet') ? 'Premium' : 'Standard' }}
                </span>
              </div>

              <div
                v-if="pkg.status === 'generating' || pkg.status === 'pending'"
                class="prog"
                role="progressbar"
                :aria-valuenow="pkg.progress || 5"
                aria-valuemin="0"
                aria-valuemax="100"
              >
                <div class="prog-fill" :style="{ width: (pkg.progress || 5) + '%' }"></div>
              </div>
              <p
                v-if="pkg.status === 'generating' || pkg.status === 'pending'"
                class="prog-msg"
              >{{ pkg.progress_message || 'Generating…' }}</p>
            </article>
          </div>
        </section>

        <hr class="ca-hair" />

        <section class="tips reveal" aria-labelledby="tips-h">
          <div class="section-head">
            <h2 id="tips-h">Getting the most from your content</h2>
          </div>
          <div class="tip-grid">
            <article class="tip ca-card">
              <span class="ca-kicker">Timing</span>
              <p>
                LinkedIn Tue–Thu 8–10am. Instagram Wed–Fri 11am–1pm.
                Facebook Tue–Thu 9am.
              </p>
            </article>
            <article class="tip ca-card">
              <span class="ca-kicker">Hashtags</span>
              <p>
                Mix 3 niche tags, 3 location tags, 3 broad community tags
                per post.
              </p>
            </article>
            <article class="tip ca-card">
              <span class="ca-kicker">Visuals</span>
              <p>
                Use the visual description as a brief for your photographer
                or an Unsplash search.
              </p>
            </article>
          </div>
        </section>
      </template>
    </main>

    <Transition name="fade">
      <div
        v-if="showGenerateModal"
        class="overlay"
        role="dialog"
        aria-modal="true"
        aria-labelledby="gen-title"
        @click.self="closeGenerate"
        @keydown.esc="closeGenerate"
      >
        <div class="modal ca-card">
          <button class="modal-close" @click="closeGenerate" aria-label="Close">×</button>
          <span class="ca-kicker">Generate</span>
          <h3 id="gen-title">30-day content package</h3>

          <div class="ca-field">
            <label for="start-date">Start date</label>
            <input id="start-date" v-model="genForm.start_date" type="date" />
          </div>

          <div class="ca-field">
            <label>Platforms</label>
            <div class="plat-check">
              <label
                v-for="p in allPlatforms"
                :key="p"
                class="plat-check-item"
              >
                <input type="checkbox" :value="p" v-model="genForm.platforms" />
                <span>{{ p }}</span>
              </label>
            </div>
          </div>

          <p v-if="genError" class="form-err">{{ genError }}</p>

          <button
            class="ca-btn"
            @click="generateContent"
            :disabled="generating || genForm.platforms.length === 0"
          >
            {{ generating ? 'Submitting…' : 'Generate package →' }}
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAgencyAuth } from '../../store/agencyAuth.js'
import {
  getMyProfile, getClientPackages, generateContent as apiGenerateContent,
} from '../../api/agency.js'
import { useReveal } from '../../composables/useReveal.js'

const router = useRouter()
const auth   = useAgencyAuth()

const root    = ref(null)
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

useReveal(root)

async function loadPortal() {
  try {
    const res = await getMyProfile()
    client.value = res.data
    await loadPackages()
  } catch {
    client.value = null
  } finally {
    loading.value = false
    await nextTick()
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

function openGenerate() {
  genError.value = ''
  showGenerateModal.value = true
}

function closeGenerate() {
  if (generating.value) return
  showGenerateModal.value = false
}

async function generateContent() {
  genError.value   = ''
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

function statusPill(status) {
  return {
    active:     'ok',
    completed:  'ok',
    onboarding: 'warn',
    pending:    'warn',
    generating: 'warn',
    paused:     'err',
    churned:    'err',
    failed:     'err',
  }[status] || ''
}
function planPill(plan) {
  return plan === 'retainer' ? 'brand' : ''
}

onMounted(async () => {
  await loadPortal()
  pollInterval = setInterval(pollGeneratingPackages, 3000)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})
</script>

<style scoped>
.portal-inner {
  max-width: var(--page);
  margin: 0 auto;
  padding: var(--s-8) var(--s-5) var(--s-10);
}

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

.empty {
  text-align: center;
  padding: var(--s-10) var(--s-4);
  max-width: 620px;
  margin: 0 auto;
}
.empty h1 { font-size: var(--display-2); margin: var(--s-3) 0 var(--s-4); }
.empty .lede { color: var(--ink-mid); font-size: var(--body-lg); margin: 0 auto var(--s-6); }

.portal-head {
  display: flex; justify-content: space-between; align-items: flex-start;
  gap: var(--s-5);
  flex-wrap: wrap;
  margin-bottom: var(--s-3);
}
.portal-head h1 { font-size: var(--display-3); margin: var(--s-2) 0; }
.head-pills { display: flex; gap: var(--s-2); flex-wrap: wrap; }

.section-head {
  display: flex; justify-content: space-between; align-items: baseline;
  margin-bottom: var(--s-6);
  flex-wrap: wrap; gap: var(--s-3);
}
.section-head h2 { font-size: var(--display-3); }
.count-mono {
  font-family: var(--font-mono);
  font-size: var(--caption);
  color: var(--ink-lo);
  letter-spacing: 0.04em;
}

.empty-soft {
  padding: var(--s-7);
  border: 1px dashed var(--hairline-2);
  border-radius: var(--r-3);
  text-align: center;
  color: var(--ink-lo);
  background: var(--surface-1);
}

.pkg-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--s-4);
}
.pkg-card {
  cursor: default;
  padding: var(--s-5);
  display: flex; flex-direction: column; gap: var(--s-3);
}
.pkg-card.completed { cursor: pointer; }
.pkg-card:focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: 3px;
}
.pkg-top { display: flex; justify-content: space-between; align-items: center; }
.pkg-month {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 1.0625rem;
  color: var(--ink-hi);
  letter-spacing: -0.02em;
}
.pkg-platforms { display: flex; flex-wrap: wrap; gap: 6px; }
.plat-tag {
  font-family: var(--font-mono);
  font-size: var(--mono-cap);
  padding: 2px 8px;
  border-radius: var(--r-full);
  background: var(--surface-2);
  color: var(--ink-mid);
  letter-spacing: 0.04em;
  text-transform: lowercase;
}
.pkg-meta {
  display: flex; justify-content: space-between;
  font-size: var(--caption);
  color: var(--ink-lo);
}
.pkg-meta .mono { font-family: var(--font-mono); letter-spacing: 0.04em; }

.prog {
  height: 3px;
  background: color-mix(in oklab, var(--ink-hi), transparent 92%);
  border-radius: var(--r-full);
  overflow: hidden;
  margin-top: var(--s-2);
}
.prog-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--brand), var(--flame));
  transition: width var(--dur-4) var(--ease-out);
}
.prog-msg {
  font-size: var(--caption);
  color: var(--ink-lo);
  margin: 0;
  font-family: var(--font-mono);
  letter-spacing: 0.03em;
}

.tip-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: var(--s-4);
}
.tip { padding: var(--s-5); }
.tip p { margin: var(--s-3) 0 0; color: var(--ink-mid); line-height: 1.6; }

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
  width: 100%; max-width: 480px;
  padding: var(--s-7);
  background: var(--paper);
  box-shadow: var(--shadow-lg);
}
.modal h3 { margin: var(--s-2) 0 var(--s-5); font-size: 1.5rem; }
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

.plat-check { display: flex; flex-wrap: wrap; gap: var(--s-3); }
.plat-check-item {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 12px;
  border: 1px solid var(--hairline);
  border-radius: var(--r-full);
  background: var(--surface-1);
  cursor: pointer;
  font-size: var(--small);
  text-transform: capitalize;
  transition: border-color var(--dur-2) var(--ease-out),
              background var(--dur-2) var(--ease-out);
}
.plat-check-item:hover { border-color: var(--hairline-2); }
.plat-check-item input { accent-color: var(--brand); }
.form-err {
  color: var(--err);
  font-size: var(--caption);
  margin: 0 0 var(--s-3);
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
