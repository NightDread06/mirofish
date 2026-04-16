<template>
  <div ref="root" class="cagency leads">
    <a href="#main" class="ca-skip">Skip to content</a>

    <nav class="ca-nav" aria-label="Leads">
      <router-link to="/agency/admin" class="nav-back">
        <span aria-hidden="true">←</span> Back to admin
      </router-link>
      <div v-if="campaign" class="nav-title">{{ campaign.name }}</div>
      <span></span>
    </nav>

    <main id="main" class="inner">
      <header v-if="campaign" class="head reveal">
        <span class="ca-kicker">Campaign</span>
        <h1>{{ campaign.name }}</h1>
        <div class="head-meta">
          <span class="ca-pill" :class="statusPill(campaign.status)">{{ campaign.status }}</span>
          <span class="ca-pill">{{ campaign.business_type }}</span>
          <span class="ca-pill">{{ campaign.target_city }}</span>
        </div>
      </header>

      <section v-if="campaign" class="funnel reveal" aria-label="Lead funnel">
        <div class="funnel-step" v-for="(step, i) in funnelSteps" :key="step.key">
          <span class="step-num">{{ campaign.metrics?.[step.key] || 0 }}</span>
          <span class="step-lbl">{{ step.label }}</span>
          <span v-if="i < funnelSteps.length - 1" class="step-arrow" aria-hidden="true">→</span>
        </div>
      </section>

      <div class="toolbar reveal">
        <div class="ca-field inline grow">
          <label for="lead-search" class="visually-hidden">Search leads</label>
          <input
            id="lead-search"
            v-model="search"
            type="text"
            placeholder="Search name or business…"
            autocomplete="off"
          />
        </div>
        <div class="ca-field inline">
          <label for="lead-stage" class="visually-hidden">Filter by stage</label>
          <select id="lead-stage" v-model="stageFilter">
            <option value="">All stages</option>
            <option v-for="s in stages" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
        <button class="ca-btn" @click="runScout" :disabled="scouting">
          {{ scouting ? 'Scouting…' : 'Run scout' }}
        </button>
        <button class="ca-btn secondary" @click="openEmailSequenceModal">
          Start email sequence
        </button>
        <button class="ca-btn ghost" @click="showImport = true">+ Import CSV</button>
      </div>

      <Transition name="toast">
        <div v-if="toast" class="toast" role="status" aria-live="polite">{{ toast }}</div>
      </Transition>

      <div v-if="loading" class="state">Loading leads…</div>
      <div v-else-if="filteredLeads.length === 0" class="empty-soft">
        No leads found.
      </div>
      <div v-else class="table-wrap reveal">
        <table class="data-table">
          <thead>
            <tr>
              <th>Business</th>
              <th>Name</th>
              <th>City</th>
              <th>Email</th>
              <th>Source</th>
              <th>Stage</th>
              <th>Notes</th>
              <th class="right">Chat</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="lead in filteredLeads" :key="lead.id">
              <td class="cell-name">{{ lead.business_name || '—' }}</td>
              <td>{{ lead.first_name || '—' }}</td>
              <td>{{ lead.city || '—' }}</td>
              <td class="cell-email">{{ lead.email || '—' }}</td>
              <td>
                <span class="src-badge" :class="lead.source">
                  {{ lead.source || '—' }}
                </span>
              </td>
              <td>
                <label :for="`stage-${lead.id}`" class="visually-hidden">Stage</label>
                <select
                  :id="`stage-${lead.id}`"
                  :value="lead.stage"
                  @change="changeStage(lead, $event.target.value)"
                  class="stage-select"
                  :class="lead.stage"
                >
                  <option v-for="s in stages" :key="s" :value="s">{{ s }}</option>
                </select>
              </td>
              <td class="cell-notes" :title="lead.notes">{{ (lead.notes || '').slice(0, 60) }}</td>
              <td class="right">
                <button class="chat-btn" @click="openChat(lead)" aria-label="Open AI chat for lead">
                  <span aria-hidden="true">💬</span>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </main>

    <Transition name="fade">
      <div
        v-if="showImport"
        class="overlay"
        role="dialog"
        aria-modal="true"
        aria-labelledby="import-title"
        @click.self="showImport = false"
        @keydown.esc="showImport = false"
      >
        <div class="modal ca-card">
          <button class="modal-close" @click="showImport = false" aria-label="Close">×</button>
          <span class="ca-kicker">Import</span>
          <h3 id="import-title">Import leads from CSV</h3>
          <p class="modal-hint">
            Paste CSV rows below. Columns:
            <code>first_name, business_name, email, linkedin_url, city</code>
          </p>
          <div class="ca-field">
            <label for="csv-input">CSV content</label>
            <textarea
              id="csv-input"
              v-model="csvText"
              rows="10"
              placeholder="John,Acme Gym,john@acmegym.ie,https://linkedin.com/in/john,Dublin"
            ></textarea>
          </div>
          <div class="modal-actions">
            <button class="ca-btn" @click="submitImport">Import</button>
            <button class="ca-btn secondary" @click="showImport = false">Cancel</button>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="fade">
      <div
        v-if="showEmailSeq"
        class="overlay"
        role="dialog"
        aria-modal="true"
        aria-labelledby="email-title"
        @click.self="showEmailSeq = false"
        @keydown.esc="showEmailSeq = false"
      >
        <div class="modal ca-card">
          <button class="modal-close" @click="showEmailSeq = false" aria-label="Close">×</button>
          <span class="ca-kicker">Sequence</span>
          <h3 id="email-title">Start email sequence</h3>
          <p class="modal-hint">
            Sends the day-0 email to all <strong>imported</strong> leads that
            have an email address and haven't started the sequence yet.
          </p>
          <div class="modal-actions">
            <button class="ca-btn" @click="confirmEmailSequence">Start sequence</button>
            <button class="ca-btn secondary" @click="showEmailSeq = false">Cancel</button>
          </div>
        </div>
      </div>
    </Transition>

    <LeadChatPanel
      v-if="chatLead"
      :lead="chatLead"
      @close="chatLead = null"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import LeadChatPanel from '../../components/agency/LeadChatPanel.vue'
import { useReveal } from '../../composables/useReveal.js'
import {
  getCampaign, listLeads, updateLead, importLeads,
  scoutCampaign, startEmailSequence,
} from '../../api/agency.js'

const route = useRoute()
const campaignId = route.params.campaignId
const root = ref(null)
useReveal(root)

const campaign = ref(null)
const leads    = ref([])
const loading  = ref(true)
const search   = ref('')
const stageFilter = ref('')
const scouting = ref(false)
const chatLead = ref(null)
const showImport   = ref(false)
const showEmailSeq = ref(false)
const csvText  = ref('')
const toast    = ref('')

const stages = [
  'imported', 'queued_message', 'connection_sent', 'connected',
  'dm_sent', 'email_sequence', 'replied', 'booked', 'closed', 'rejected',
]

const funnelSteps = [
  { key: 'total',     label: 'Total' },
  { key: 'connected', label: 'Connected' },
  { key: 'replied',   label: 'Replied' },
  { key: 'booked',    label: 'Booked' },
  { key: 'closed',    label: 'Closed' },
]

const filteredLeads = computed(() => {
  const q = search.value.toLowerCase()
  return leads.value.filter(l => {
    const matchSearch = !q
      || (l.first_name || '').toLowerCase().includes(q)
      || (l.business_name || '').toLowerCase().includes(q)
      || (l.email || '').toLowerCase().includes(q)
    const matchStage = !stageFilter.value || l.stage === stageFilter.value
    return matchSearch && matchStage
  })
})

onMounted(async () => {
  try {
    const [cRes, lRes] = await Promise.all([
      getCampaign(campaignId),
      listLeads(campaignId, { limit: 500 }),
    ])
    campaign.value = cRes.data.data
    leads.value    = lRes.data.data || []
  } catch {
    showToast('Failed to load leads')
  } finally {
    loading.value = false
  }
})

async function changeStage(lead, newStage) {
  try {
    const res = await updateLead(lead.id, { stage: newStage })
    const idx = leads.value.findIndex(l => l.id === lead.id)
    if (idx !== -1) leads.value[idx] = res.data.data
    showToast(`Stage updated → ${newStage}`)
  } catch {
    showToast('Failed to update stage')
  }
}

async function runScout() {
  scouting.value = true
  try {
    const res = await scoutCampaign(campaignId, 20)
    const count = res.data.data?.created || 0
    showToast(`Scout found ${count} new leads`)
    if (count > 0) {
      const lRes = await listLeads(campaignId, { limit: 500 })
      leads.value = lRes.data.data || []
      const cRes  = await getCampaign(campaignId)
      campaign.value = cRes.data.data
    }
  } catch (e) {
    const msg = e?.response?.data?.error || 'Scout failed'
    showToast(msg)
  } finally {
    scouting.value = false
  }
}

function openEmailSequenceModal() {
  showEmailSeq.value = true
}

async function confirmEmailSequence() {
  showEmailSeq.value = false
  try {
    const res = await startEmailSequence(campaignId)
    showToast(`Email sequence started for ${res.data.data?.started || 0} leads`)
    const lRes = await listLeads(campaignId, { limit: 500 })
    leads.value = lRes.data.data || []
  } catch (e) {
    const msg = e?.response?.data?.error || 'Failed to start email sequence'
    showToast(msg)
  }
}

function openChat(lead) { chatLead.value = lead }

async function submitImport() {
  // Safety: cap CSV size so a paste of a 10MB file doesn't freeze the UI
  const text = (csvText.value || '').slice(0, 2_000_000)
  const rows = text.trim().split('\n').filter(Boolean).slice(0, 5000)
  const parsed = rows
    .map(row => row.slice(0, 2000))
    .map(row => {
      const [first_name, business_name, email, linkedin_url, city] = row.split(',').map(s => (s || '').trim())
      return { first_name, business_name, email, linkedin_url, city, source: 'manual' }
    })
    .filter(r => r.business_name)

  if (!parsed.length) { showToast('No valid rows found'); return }
  try {
    const res = await importLeads(campaignId, parsed)
    showToast(`Imported ${res.data.data.created} leads`)
    showImport.value = false
    csvText.value    = ''
    const lRes = await listLeads(campaignId, { limit: 500 })
    leads.value = lRes.data.data || []
    const cRes  = await getCampaign(campaignId)
    campaign.value = cRes.data.data
  } catch {
    showToast('Import failed')
  }
}

function showToast(msg) {
  toast.value = msg
  setTimeout(() => { toast.value = '' }, 3000)
}

function statusPill(s) {
  return { active: 'ok', draft: 'warn', paused: 'err' }[s] || ''
}
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
  max-width: 1400px;
  margin: 0 auto;
  padding: var(--s-7) var(--s-5) var(--s-10);
}

.head { margin-bottom: var(--s-6); }
.head h1 { font-size: var(--display-3); margin: var(--s-2) 0 var(--s-3); }
.head-meta { display: flex; gap: var(--s-2); flex-wrap: wrap; }

.funnel {
  display: flex; flex-wrap: wrap; align-items: center;
  gap: var(--s-4);
  padding: var(--s-5);
  border: 1px solid var(--hairline);
  border-radius: var(--r-3);
  background: var(--surface-1);
  margin-bottom: var(--s-5);
}
.funnel-step { display: flex; align-items: center; gap: var(--s-3); }
.step-num {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 1.5rem;
  letter-spacing: -0.02em;
  color: var(--ink-hi);
  font-variant-numeric: tabular-nums;
}
.step-lbl {
  font-family: var(--font-mono);
  font-size: var(--mono-cap);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--ink-lo);
}
.step-arrow { color: var(--ink-lo); font-family: var(--font-mono); }

.toolbar {
  display: flex; gap: var(--s-3);
  margin-bottom: var(--s-4);
  flex-wrap: wrap;
  align-items: center;
}
.ca-field.inline { margin: 0; }
.ca-field.inline.grow { flex: 1; min-width: 200px; }
.ca-field.inline input,
.ca-field.inline select {
  padding: 10px 14px;
  font-size: var(--small);
}

.toast {
  margin-bottom: var(--s-3);
  background: var(--ink-hi);
  color: var(--paper);
  padding: 10px 18px;
  border-radius: var(--r-2);
  font-size: var(--small);
  box-shadow: var(--shadow-md);
  width: fit-content;
}
.toast-enter-active, .toast-leave-active {
  transition: opacity var(--dur-2) var(--ease-out),
              transform var(--dur-3) var(--ease-out);
}
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(-6px); }

.state {
  padding: var(--s-7);
  text-align: center;
  color: var(--ink-lo);
}
.empty-soft {
  padding: var(--s-7);
  border: 1px dashed var(--hairline-2);
  border-radius: var(--r-3);
  text-align: center;
  color: var(--ink-lo);
  background: var(--surface-1);
}

.table-wrap {
  border: 1px solid var(--hairline);
  border-radius: var(--r-3);
  overflow-x: auto;
  background: var(--paper);
}
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--caption);
}
.data-table th {
  text-align: left;
  padding: 12px 14px;
  background: var(--surface-1);
  border-bottom: 1px solid var(--hairline);
  font-family: var(--font-mono);
  font-size: var(--mono-cap);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink-mid);
  font-weight: 500;
  white-space: nowrap;
}
.data-table td {
  padding: 12px 14px;
  border-bottom: 1px solid var(--hairline);
  color: var(--ink);
  vertical-align: middle;
}
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: var(--surface-1); }

.cell-name { font-weight: 500; color: var(--ink-hi); max-width: 180px; }
.cell-email {
  color: var(--ink-mid);
  max-width: 180px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  font-family: var(--font-mono);
  font-size: var(--mono-cap);
  letter-spacing: 0.02em;
}
.cell-notes {
  color: var(--ink-lo);
  max-width: 200px;
  font-size: 0.78rem;
  overflow: hidden; text-overflow: ellipsis;
}
.right { text-align: right; }

.src-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--r-full);
  font-family: var(--font-mono);
  font-size: var(--mono-cap);
  letter-spacing: 0.04em;
  background: var(--surface-2);
  color: var(--ink-mid);
  border: 1px solid var(--hairline);
}
.src-badge.google_maps {
  color: oklch(0.42 0.15 260);
  background: color-mix(in oklab, oklch(0.42 0.15 260), var(--paper) 92%);
  border-color: color-mix(in oklab, oklch(0.42 0.15 260), transparent 70%);
}
.src-badge.linkedin_script {
  color: var(--ok);
  background: color-mix(in oklab, var(--ok), var(--paper) 92%);
  border-color: color-mix(in oklab, var(--ok), transparent 70%);
}

.stage-select {
  padding: 4px 10px;
  border: 1px solid var(--hairline);
  border-radius: var(--r-full);
  font: inherit; font-size: var(--mono-cap);
  font-family: var(--font-mono);
  letter-spacing: 0.04em;
  background: var(--paper);
  color: var(--ink);
  cursor: pointer;
  transition: border-color var(--dur-2) var(--ease-out);
}
.stage-select:hover { border-color: var(--ink-hi); }
.stage-select:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }
.stage-select.replied  { color: var(--ok);  border-color: color-mix(in oklab, var(--ok), transparent 60%); }
.stage-select.closed   { color: var(--ok);  background: color-mix(in oklab, var(--ok), var(--paper) 92%); border-color: color-mix(in oklab, var(--ok), transparent 55%); }
.stage-select.booked   { color: var(--brand); border-color: color-mix(in oklab, var(--brand), transparent 60%); }
.stage-select.rejected { color: var(--err); border-color: color-mix(in oklab, var(--err), transparent 60%); }
.stage-select.email_sequence { color: oklch(0.45 0.15 75); border-color: color-mix(in oklab, var(--flame), transparent 60%); }

.chat-btn {
  width: 32px; height: 32px;
  border-radius: var(--r-full);
  border: 1px solid var(--hairline);
  background: var(--paper);
  cursor: pointer;
  font-size: 1rem; line-height: 1;
  transition: border-color var(--dur-2) var(--ease-out),
              background var(--dur-2) var(--ease-out);
}
.chat-btn:hover { border-color: var(--ink-hi); background: var(--surface-1); }
.chat-btn:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }

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
  width: 100%; max-width: 560px;
  max-height: 92vh; overflow-y: auto;
  padding: var(--s-7);
  background: var(--paper);
  box-shadow: var(--shadow-lg);
}
.modal h3 { font-size: 1.5rem; margin: var(--s-2) 0 var(--s-3); }
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
.modal-hint {
  font-size: var(--small);
  color: var(--ink-mid);
  line-height: 1.6;
  margin: 0 0 var(--s-4);
}
.modal-hint code {
  font-family: var(--font-mono);
  font-size: 0.82rem;
  background: var(--surface-2);
  padding: 1px 6px;
  border-radius: var(--r-1);
}
.modal-actions {
  display: flex; gap: var(--s-2);
  margin-top: var(--s-4);
}

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
