<template>
  <div ref="root" class="cagency admin">
    <a href="#main" class="ca-skip">Skip to content</a>

    <nav class="ca-nav" aria-label="Admin">
      <router-link to="/agency" class="ca-brand">
        <span class="dot" aria-hidden="true"></span>ContentAgency
      </router-link>
      <div class="ca-nav-links">
        <router-link to="/agency/portal">Portal</router-link>
        <span class="admin-tag">Admin</span>
      </div>
    </nav>

    <main id="main" class="admin-inner">
      <header class="admin-head reveal">
        <span class="ca-kicker">Operations</span>
        <h1>Dashboard</h1>
      </header>

      <section v-if="metrics" class="metrics reveal" aria-label="Business metrics">
        <article class="metric">
          <span class="m-num">€<CountUp :to="metrics.mrr_eur || 0" /></span>
          <span class="m-lbl">Monthly recurring revenue</span>
        </article>
        <article class="metric">
          <span class="m-num"><CountUp :to="metrics.active_clients || 0" /></span>
          <span class="m-lbl">Active clients</span>
        </article>
        <article class="metric">
          <span class="m-num"><CountUp :to="metrics.pilot_clients || 0" /></span>
          <span class="m-lbl">On Pilot · €500</span>
        </article>
        <article class="metric">
          <span class="m-num"><CountUp :to="metrics.retainer_clients || 0" /></span>
          <span class="m-lbl">On Retainer · €1,500</span>
        </article>
        <article class="metric">
          <span class="m-num"><CountUp :to="metrics.packages_generated || 0" /></span>
          <span class="m-lbl">Packages generated</span>
        </article>
      </section>

      <div class="tabs reveal" role="tablist">
        <button
          v-for="t in tabsDef"
          :key="t.key"
          :class="['tab', { active: activeTab === t.key }]"
          role="tab"
          :aria-selected="activeTab === t.key"
          @click="t.key === 'scheduler' ? loadScheduler() : (activeTab = t.key)"
        >{{ t.label }}</button>
      </div>

      <section v-if="activeTab === 'clients'" class="clients-section reveal">
        <div class="section-head">
          <h2>Clients</h2>
          <div class="ca-field inline">
            <label for="client-filter" class="visually-hidden">Status filter</label>
            <select id="client-filter" v-model="clientFilter">
              <option value="">All statuses</option>
              <option value="onboarding">Onboarding</option>
              <option value="active">Active</option>
              <option value="paused">Paused</option>
              <option value="churned">Churned</option>
            </select>
          </div>
        </div>

        <div v-if="loadingClients" class="load">Loading…</div>
        <div v-else class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Business</th>
                <th>Type</th>
                <th>City</th>
                <th>Plan</th>
                <th>Status</th>
                <th>Joined</th>
                <th class="right">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in filteredClients" :key="c.id">
                <td class="cell-name">{{ c.business_name }}</td>
                <td class="cell-mono">{{ c.business_type }}</td>
                <td>{{ c.city }}</td>
                <td><span class="ca-pill" :class="planPill(c.plan)">{{ c.plan }}</span></td>
                <td><span class="ca-pill" :class="statusPill(c.status)">{{ c.status }}</span></td>
                <td class="cell-mono">{{ formatDate(c.created_at) }}</td>
                <td class="right">
                  <button class="row-btn" @click="generateForClient(c)">Generate</button>
                  <button class="row-btn danger" @click="confirmDelete(c)">Delete</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section v-if="activeTab === 'outreach'" class="outreach-section reveal">
        <div class="section-head">
          <h2>Outreach campaigns</h2>
          <button class="ca-btn" @click="showNewCampaign = true">+ New campaign</button>
        </div>

        <div v-if="loadingCampaigns" class="load">Loading…</div>
        <div v-else-if="campaigns.length === 0" class="empty-soft">
          No campaigns yet. Create one to generate LinkedIn DM templates.
        </div>
        <div v-else class="camp-grid">
          <article
            v-for="c in campaigns"
            :key="c.id"
            class="camp ca-card hoverable"
          >
            <header class="camp-head" @click="openCampaign(c)">
              <span class="camp-title">{{ c.name }}</span>
              <span class="ca-pill" :class="statusPill(c.status)">{{ c.status }}</span>
            </header>
            <div class="camp-meta">
              <span>{{ c.business_type }}</span>
              <span class="sep" aria-hidden="true">·</span>
              <span>{{ c.target_city }}</span>
            </div>
            <div class="camp-funnel">
              <span>{{ c.metrics?.total || 0 }} leads</span>
              <span class="arr" aria-hidden="true">→</span>
              <span>{{ c.metrics?.connected || 0 }} connected</span>
              <span class="arr" aria-hidden="true">→</span>
              <span>{{ c.metrics?.replied || 0 }} replied</span>
              <span class="arr" aria-hidden="true">→</span>
              <strong>{{ c.metrics?.closed || 0 }} closed</strong>
            </div>
            <footer class="camp-actions">
              <button class="row-btn" @click="router.push(`/agency/admin/leads/${c.id}`)">
                View leads →
              </button>
              <button class="row-btn" @click="openCampaign(c)">Templates</button>
            </footer>
          </article>
        </div>
      </section>

      <section v-if="activeTab === 'scheduler'" class="scheduler-section reveal">
        <div class="section-head">
          <h2>Autonomous scheduler</h2>
          <div class="sched-ctrl">
            <span class="sched-status" :class="{ on: schedulerStatus?.running, off: !schedulerStatus?.running }">
              <span class="dot" aria-hidden="true"></span>
              {{ schedulerStatus?.running ? 'Running' : 'Stopped' }}
            </span>
            <button class="row-btn" @click="pauseAll">Pause all</button>
            <button class="row-btn" @click="resumeAll">Resume all</button>
          </div>
        </div>

        <div v-if="loadingScheduler" class="load">Loading…</div>
        <div v-else-if="schedulerStatus" class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Job</th>
                <th>ID</th>
                <th>Next run</th>
                <th class="right">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="job in schedulerStatus.jobs" :key="job.id">
                <td class="cell-name">{{ job.name }}</td>
                <td><code class="code">{{ job.id }}</code></td>
                <td class="cell-mono">
                  {{ job.next_run_time ? formatDate(job.next_run_time) : 'Paused' }}
                </td>
                <td class="right">
                  <button class="row-btn" @click="triggerJob(job.id)">
                    {{ triggeringJob === job.id ? 'Running…' : 'Run now' }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <aside class="sched-help">
          <span class="ca-kicker">Jobs</span>
          <ul>
            <li><code class="code">daily_scout</code> — 08:00 daily: import new prospects from Google Maps</li>
            <li><code class="code">check_replies</code> — every 15 min: poll inbox, run AI chat closer, send replies</li>
            <li><code class="code">follow_ups</code> — every 30 min: send day-3 and day-7 sequence emails</li>
            <li><code class="code">publish_posts</code> — 23:00 daily: push tomorrow's approved posts to Buffer</li>
          </ul>
        </aside>
      </section>
    </main>

    <Transition name="fade">
      <div
        v-if="showNewCampaign"
        class="overlay"
        role="dialog"
        aria-modal="true"
        aria-labelledby="camp-title"
        @click.self="showNewCampaign = false"
        @keydown.esc="showNewCampaign = false"
      >
        <div class="modal ca-card">
          <button class="modal-close" @click="showNewCampaign = false" aria-label="Close">×</button>
          <span class="ca-kicker">New campaign</span>
          <h3 id="camp-title">Create outreach campaign</h3>

          <div class="ca-field">
            <label for="camp-name">Campaign name</label>
            <input
              id="camp-name"
              v-model="newCampaign.name"
              type="text"
              placeholder="e.g. Gyms Dublin Q2 2026"
              autocomplete="off"
            />
          </div>
          <div class="ca-field">
            <label for="camp-type">Business type</label>
            <select id="camp-type" v-model="newCampaign.business_type">
              <option value="gym">Gym</option>
              <option value="salon">Salon</option>
              <option value="restaurant">Restaurant</option>
              <option value="clinic">Clinic</option>
              <option value="real_estate">Real Estate</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div class="ca-field">
            <label for="camp-city">Target city</label>
            <input
              id="camp-city"
              v-model="newCampaign.target_city"
              type="text"
              placeholder="e.g. Dublin"
              autocomplete="off"
            />
          </div>

          <p class="form-hint">
            Claude will generate LinkedIn DM templates and a Loom script
            for this campaign.
          </p>
          <p v-if="campaignError" class="form-err">{{ campaignError }}</p>

          <button class="ca-btn" @click="createNewCampaign" :disabled="creatingCampaign">
            {{ creatingCampaign ? 'Generating templates…' : 'Create campaign →' }}
          </button>
        </div>
      </div>
    </Transition>

    <Transition name="fade">
      <div
        v-if="selectedCampaign"
        class="overlay"
        role="dialog"
        aria-modal="true"
        aria-labelledby="camp-detail-title"
        @click.self="selectedCampaign = null"
        @keydown.esc="selectedCampaign = null"
      >
        <div class="modal camp-detail-modal ca-card">
          <button class="modal-close" @click="selectedCampaign = null" aria-label="Close">×</button>
          <h2 id="camp-detail-title" class="visually-hidden">Campaign templates</h2>
          <OutreachTemplates :campaign="selectedCampaign" />
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h } from 'vue'
import {
  getDashboardMetrics, getClients, listCampaigns, createCampaign,
  getSchedulerStatus, runSchedulerJob, pauseScheduler, resumeScheduler,
} from '../../api/agency.js'
import OutreachTemplates from '../../components/agency/OutreachTemplates.vue'
import { useRouter } from 'vue-router'
import { useReveal } from '../../composables/useReveal.js'

const router = useRouter()
const root   = ref(null)
useReveal(root)

const metrics        = ref(null)
const clients        = ref([])
const campaigns      = ref([])
const loadingClients   = ref(true)
const loadingCampaigns = ref(true)
const activeTab      = ref('clients')
const clientFilter   = ref('')
const showNewCampaign  = ref(false)
const selectedCampaign = ref(null)
const creatingCampaign = ref(false)
const campaignError    = ref('')

const schedulerStatus  = ref(null)
const loadingScheduler = ref(false)
const triggeringJob    = ref('')

const newCampaign = ref({ name: '', business_type: 'gym', target_city: '' })

const tabsDef = [
  { key: 'clients',   label: 'Clients' },
  { key: 'outreach',  label: 'Outreach campaigns' },
  { key: 'scheduler', label: 'Scheduler' },
]

const filteredClients = computed(() => {
  if (!clientFilter.value) return clients.value
  return clients.value.filter(c => c.status === clientFilter.value)
})

function formatDate(iso) {
  return iso ? new Date(iso).toLocaleDateString('en-IE', { day: 'numeric', month: 'short', year: 'numeric' }) : ''
}

function openCampaign(c) { selectedCampaign.value = c }

async function generateForClient() {
  router.push(`/agency/portal`)
}

function confirmDelete(client) {
  if (confirm(`Delete all data for ${client.business_name}? This is irreversible (GDPR erasure).`)) {
    import('../../api/agency.js').then(({ gdprDeleteClient }) => {
      gdprDeleteClient(client.id).then(() => {
        clients.value = clients.value.filter(c => c.id !== client.id)
      })
    })
  }
}

async function createNewCampaign() {
  if (!newCampaign.value.name.trim()) { campaignError.value = 'Name required'; return }
  campaignError.value = ''
  creatingCampaign.value = true
  try {
    const res = await createCampaign(newCampaign.value)
    campaigns.value.unshift(res.data)
    showNewCampaign.value = false
    newCampaign.value = { name: '', business_type: 'gym', target_city: '' }
  } catch (err) {
    campaignError.value = err?.message || 'Failed to create campaign'
  } finally {
    creatingCampaign.value = false
  }
}

async function loadScheduler() {
  activeTab.value = 'scheduler'
  if (schedulerStatus.value) return
  loadingScheduler.value = true
  try {
    const res = await getSchedulerStatus()
    schedulerStatus.value = res.data.data
  } catch { /* scheduler may not be running */ }
  finally { loadingScheduler.value = false }
}

async function triggerJob(jobId) {
  triggeringJob.value = jobId
  try {
    await runSchedulerJob(jobId)
    setTimeout(() => { triggeringJob.value = '' }, 3000)
  } catch { triggeringJob.value = '' }
}

async function pauseAll() {
  await pauseScheduler()
  schedulerStatus.value = null
  await loadScheduler()
}

async function resumeAll() {
  await resumeScheduler()
  schedulerStatus.value = null
  await loadScheduler()
}

function statusPill(s) {
  return {
    active: 'ok', completed: 'ok',
    onboarding: 'warn', draft: 'warn',
    paused: 'err', churned: 'err',
  }[s] || ''
}
function planPill(plan) { return plan === 'retainer' ? 'brand' : '' }

/**
 * CountUp: animates a numeric value from 0 to `to` over ~800ms.
 * Respects prefers-reduced-motion (renders the target value immediately).
 */
const CountUp = {
  props: { to: { type: Number, required: true } },
  setup(props) {
    const cur = ref(0)
    const reduce = typeof window !== 'undefined'
      && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

    if (reduce) {
      cur.value = props.to
    } else {
      const start = performance.now()
      const dur = 800
      const from = 0
      const diff = props.to - from
      const tick = (t) => {
        const p = Math.min(1, (t - start) / dur)
        const eased = 1 - Math.pow(1 - p, 3)
        cur.value = Math.round(from + diff * eased)
        if (p < 1) requestAnimationFrame(tick)
      }
      requestAnimationFrame(tick)
    }
    return () => h('span', cur.value.toLocaleString('en-IE'))
  },
}

onMounted(async () => {
  const [m, c, camp] = await Promise.allSettled([
    getDashboardMetrics(),
    getClients(),
    listCampaigns(),
  ])
  if (m.status === 'fulfilled') metrics.value = m.value.data?.data || m.value.data
  if (c.status === 'fulfilled') clients.value = c.value.data?.data || c.value.data || []
  if (camp.status === 'fulfilled') campaigns.value = camp.value.data?.data || camp.value.data || []
  loadingClients.value = false
  loadingCampaigns.value = false
})
</script>

<style scoped>
.admin-tag {
  font-family: var(--font-mono);
  font-size: var(--mono-cap);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  padding: 4px 10px;
  background: var(--ink-hi);
  color: var(--paper);
  border-radius: var(--r-full);
}

.admin-inner {
  max-width: var(--page);
  margin: 0 auto;
  padding: var(--s-8) var(--s-5) var(--s-10);
}

.admin-head h1 { font-size: var(--display-2); margin: var(--s-2) 0 0; }
.admin-head { margin-bottom: var(--s-8); }

.metrics {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: var(--s-4);
  margin-bottom: var(--s-8);
}
.metric {
  padding: var(--s-5);
  background: var(--paper);
  border: 1px solid var(--hairline);
  border-radius: var(--r-3);
  display: flex; flex-direction: column; gap: 6px;
}
.m-num {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 2.25rem;
  letter-spacing: -0.03em;
  line-height: 1;
  color: var(--ink-hi);
  font-variant-numeric: tabular-nums;
}
.m-lbl {
  font-family: var(--font-mono);
  font-size: var(--mono-cap);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--ink-lo);
}

.tabs {
  display: flex; gap: var(--s-2);
  border-bottom: 1px solid var(--hairline);
  margin-bottom: var(--s-7);
  flex-wrap: wrap;
}
.tab {
  padding: 12px 22px;
  background: transparent; border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer; font: inherit;
  font-size: var(--small); color: var(--ink-lo);
  margin-bottom: -1px;
  transition: color var(--dur-2) var(--ease-out),
              border-color var(--dur-2) var(--ease-out);
}
.tab:hover { color: var(--ink-hi); }
.tab.active { color: var(--ink-hi); border-bottom-color: var(--ink-hi); font-weight: 500; }
.tab:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; border-radius: var(--r-1); }

.section-head {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: var(--s-5); flex-wrap: wrap; gap: var(--s-3);
}
.section-head h2 { font-size: var(--display-3); }
.ca-field.inline {
  margin: 0;
}
.ca-field.inline select {
  padding: 8px 12px;
  font-size: var(--small);
}

.load { color: var(--ink-lo); padding: var(--s-6) 0; text-align: center; }
.empty-soft {
  padding: var(--s-7);
  border: 1px dashed var(--hairline-2);
  border-radius: var(--r-3);
  text-align: center; color: var(--ink-lo);
  background: var(--surface-1);
}

.table-wrap {
  border: 1px solid var(--hairline);
  border-radius: var(--r-3);
  overflow: hidden;
  background: var(--paper);
}
.data-table { width: 100%; border-collapse: collapse; }
.data-table th {
  text-align: left;
  padding: 14px 18px;
  background: var(--surface-1);
  border-bottom: 1px solid var(--hairline);
  font-family: var(--font-mono);
  font-size: var(--mono-cap);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink-mid);
  font-weight: 500;
}
.data-table td {
  padding: 14px 18px;
  border-bottom: 1px solid var(--hairline);
  font-size: var(--small);
  color: var(--ink);
}
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: var(--surface-1); }
.cell-name { font-weight: 500; color: var(--ink-hi); }
.cell-mono { font-family: var(--font-mono); font-size: var(--mono-cap); color: var(--ink-mid); letter-spacing: 0.02em; }
.right { text-align: right; }

.row-btn {
  padding: 6px 12px;
  font-family: var(--font-body);
  font-size: var(--caption);
  border: 1px solid var(--hairline);
  background: var(--paper);
  color: var(--ink);
  cursor: pointer;
  border-radius: var(--r-full);
  margin-left: 6px;
  transition: all var(--dur-2) var(--ease-out);
}
.row-btn:first-child { margin-left: 0; }
.row-btn:hover { border-color: var(--ink-hi); }
.row-btn:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }
.row-btn.danger { color: var(--err); border-color: color-mix(in oklab, var(--err), transparent 60%); }
.row-btn.danger:hover { background: color-mix(in oklab, var(--err), var(--paper) 92%); }

.camp-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--s-4);
}
.camp { padding: var(--s-5); display: flex; flex-direction: column; gap: var(--s-3); }
.camp-head {
  display: flex; justify-content: space-between; align-items: center;
  gap: var(--s-2); cursor: pointer;
}
.camp-title {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 1.0625rem;
  letter-spacing: -0.015em;
  color: var(--ink-hi);
}
.camp-meta {
  font-family: var(--font-mono);
  font-size: var(--mono-cap);
  letter-spacing: 0.04em;
  color: var(--ink-lo);
}
.camp-meta .sep { margin: 0 6px; }
.camp-funnel {
  display: flex; flex-wrap: wrap; gap: 6px;
  font-size: var(--small);
  color: var(--ink-mid);
  align-items: center;
}
.camp-funnel strong { color: var(--ink-hi); font-weight: 600; }
.camp-funnel .arr { color: var(--ink-lo); }
.camp-actions {
  display: flex; gap: var(--s-2);
  padding-top: var(--s-3);
  border-top: 1px solid var(--hairline);
}

.sched-ctrl { display: flex; align-items: center; gap: var(--s-3); flex-wrap: wrap; }
.sched-status {
  display: inline-flex; align-items: center; gap: 6px;
  font-family: var(--font-mono);
  font-size: var(--mono-cap);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 4px 10px;
  border-radius: var(--r-full);
  border: 1px solid;
}
.sched-status.on { color: var(--ok); border-color: color-mix(in oklab, var(--ok), transparent 60%); background: color-mix(in oklab, var(--ok), var(--paper) 92%); }
.sched-status.off { color: var(--ink-lo); border-color: var(--hairline); background: var(--surface-1); }
.sched-status .dot {
  width: 6px; height: 6px; border-radius: 50%; background: currentColor;
}
.sched-status.on .dot { animation: pulse 1.6s var(--ease-in-out) infinite; }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.35; } }

.code {
  font-family: var(--font-mono);
  font-size: 0.82rem;
  padding: 1px 8px;
  background: var(--surface-2);
  border-radius: var(--r-1);
  color: var(--ink-hi);
}
.sched-help {
  margin-top: var(--s-6);
  padding: var(--s-5);
  background: var(--surface-1);
  border: 1px solid var(--hairline);
  border-radius: var(--r-3);
}
.sched-help ul { margin: var(--s-3) 0 0; padding-left: var(--s-5); }
.sched-help li {
  font-size: var(--small);
  color: var(--ink);
  line-height: 1.7;
  margin-bottom: 6px;
}

.form-hint { font-size: var(--caption); color: var(--ink-lo); margin: 0 0 var(--s-3); }
.form-err { font-size: var(--caption); color: var(--err); margin: 0 0 var(--s-3); }

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
  width: 100%; max-width: 520px;
  max-height: 92vh;
  overflow-y: auto;
  padding: var(--s-7);
  background: var(--paper);
  box-shadow: var(--shadow-lg);
}
.camp-detail-modal { max-width: 780px; }
.modal h3 { font-size: 1.5rem; margin: var(--s-2) 0 var(--s-5); }
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
