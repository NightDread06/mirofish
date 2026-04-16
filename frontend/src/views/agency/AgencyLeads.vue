<template>
  <div class="leads-page">
    <!-- Header -->
    <div class="page-header">
      <button class="btn-back" @click="$router.push('/agency/admin')">← Back to Admin</button>
      <div class="header-info" v-if="campaign">
        <h1>{{ campaign.name }}</h1>
        <div class="header-meta">
          <span class="badge" :class="campaign.status">{{ campaign.status }}</span>
          <span class="meta-tag">{{ campaign.business_type }}</span>
          <span class="meta-tag">{{ campaign.target_city }}</span>
        </div>
      </div>
    </div>

    <!-- Funnel stats -->
    <div v-if="campaign" class="funnel-bar">
      <div class="funnel-step" v-for="step in funnelSteps" :key="step.key">
        <div class="funnel-val">{{ campaign.metrics?.[step.key] || 0 }}</div>
        <div class="funnel-label">{{ step.label }}</div>
      </div>
    </div>

    <!-- Toolbar -->
    <div class="toolbar">
      <input v-model="search" class="search-input" placeholder="Search name or business…" />
      <select v-model="stageFilter" class="stage-filter">
        <option value="">All stages</option>
        <option v-for="s in stages" :key="s" :value="s">{{ s }}</option>
      </select>
      <button class="btn-action" @click="runScout" :disabled="scouting">
        {{ scouting ? 'Scouting…' : '🔍 Run Scout' }}
      </button>
      <button class="btn-action" @click="openEmailSequenceModal">
        ✉ Start Email Sequence
      </button>
      <button class="btn-action" @click="showImport = true">+ Import CSV</button>
    </div>

    <!-- Toast -->
    <div v-if="toast" class="toast">{{ toast }}</div>

    <!-- Leads table -->
    <div v-if="loading" class="loading">Loading leads…</div>
    <div v-else-if="filteredLeads.length === 0" class="empty">No leads found.</div>
    <table v-else class="leads-table">
      <thead>
        <tr>
          <th>Business</th>
          <th>Name</th>
          <th>City</th>
          <th>Email</th>
          <th>Source</th>
          <th>Stage</th>
          <th>Notes</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="lead in filteredLeads" :key="lead.id">
          <td class="cell-business">{{ lead.business_name || '—' }}</td>
          <td>{{ lead.first_name || '—' }}</td>
          <td>{{ lead.city || '—' }}</td>
          <td class="cell-email">{{ lead.email || '—' }}</td>
          <td><span class="source-badge" :class="lead.source">{{ lead.source }}</span></td>
          <td>
            <select :value="lead.stage" @change="changeStage(lead, $event.target.value)"
                    class="stage-select" :class="lead.stage">
              <option v-for="s in stages" :key="s" :value="s">{{ s }}</option>
            </select>
          </td>
          <td class="cell-notes" :title="lead.notes">{{ (lead.notes || '').slice(0, 60) }}</td>
          <td class="cell-actions">
            <button class="btn-chat" @click="openChat(lead)" title="AI Chat Conversation">💬</button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Import CSV modal -->
    <div v-if="showImport" class="modal-overlay" @click.self="showImport = false">
      <div class="modal">
        <h3>Import Leads from CSV</h3>
        <p class="modal-hint">Paste CSV rows below. Columns: first_name, business_name, email, linkedin_url, city</p>
        <textarea v-model="csvText" class="csv-input" rows="10"
          placeholder="John,Acme Gym,john@acmegym.ie,https://linkedin.com/in/john,Dublin"></textarea>
        <div class="modal-actions">
          <button class="btn-primary" @click="submitImport">Import</button>
          <button class="btn-ghost" @click="showImport = false">Cancel</button>
        </div>
      </div>
    </div>

    <!-- Email sequence modal -->
    <div v-if="showEmailSeq" class="modal-overlay" @click.self="showEmailSeq = false">
      <div class="modal">
        <h3>Start Email Sequence</h3>
        <p class="modal-hint">
          Sends Day-0 email to all <strong>imported</strong> leads that have an email address
          and haven't started the sequence yet.
        </p>
        <div class="modal-actions">
          <button class="btn-primary" @click="confirmEmailSequence">Start sequence</button>
          <button class="btn-ghost" @click="showEmailSeq = false">Cancel</button>
        </div>
      </div>
    </div>

    <!-- AI Chat panel -->
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
import {
  getCampaign, listLeads, updateLead, importLeads,
  scoutCampaign, startEmailSequence,
} from '../../api/agency.js'

const route = useRoute()
const campaignId = route.params.campaignId

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
  } catch (e) {
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

function openChat(lead) {
  chatLead.value = lead
}

async function submitImport() {
  const rows = csvText.value.trim().split('\n').filter(Boolean)
  const parsed = rows.map(row => {
    const [first_name, business_name, email, linkedin_url, city] = row.split(',').map(s => s.trim())
    return { first_name, business_name, email, linkedin_url, city, source: 'manual' }
  }).filter(r => r.business_name)

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
</script>

<style scoped>
.leads-page { font-family: 'Courier New', monospace; padding: 24px; max-width: 1400px; margin: 0 auto; }

.page-header { display: flex; align-items: flex-start; gap: 20px; margin-bottom: 20px; }
.btn-back { background: none; border: 1px solid #ddd; padding: 6px 14px; cursor: pointer; font-family: inherit; font-size: 0.85rem; }
.header-info h1 { font-size: 1.4rem; margin-bottom: 6px; }
.header-meta { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.badge { padding: 3px 10px; font-size: 0.78rem; border: 1px solid; }
.badge.active { border-color: #090; color: #090; }
.badge.draft  { border-color: #f90; color: #f90; }
.badge.paused { border-color: #888; color: #888; }
.meta-tag { background: #f0f0f0; padding: 3px 10px; font-size: 0.78rem; }

.funnel-bar { display: flex; gap: 24px; padding: 16px; background: #f9f9f9; border: 1px solid #eee; margin-bottom: 20px; flex-wrap: wrap; }
.funnel-step { text-align: center; }
.funnel-val { font-size: 1.4rem; font-weight: bold; }
.funnel-label { font-size: 0.72rem; color: #888; text-transform: uppercase; }

.toolbar { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; align-items: center; }
.search-input { padding: 8px 12px; border: 1px solid #ddd; font-family: inherit; font-size: 0.85rem; min-width: 200px; flex: 1; }
.stage-filter { padding: 8px 12px; border: 1px solid #ddd; font-family: inherit; font-size: 0.85rem; }
.btn-action { padding: 8px 16px; background: #111; color: #fff; border: none; cursor: pointer; font-family: inherit; font-size: 0.85rem; }
.btn-action:disabled { background: #999; cursor: not-allowed; }

.toast { background: #111; color: #fff; padding: 10px 20px; margin-bottom: 12px; font-size: 0.85rem; }
.loading, .empty { padding: 40px; text-align: center; color: #888; }

.leads-table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
.leads-table th { background: #111; color: #fff; padding: 10px 12px; text-align: left; font-size: 0.75rem; text-transform: uppercase; }
.leads-table td { padding: 10px 12px; border-bottom: 1px solid #eee; vertical-align: middle; }
.leads-table tr:hover td { background: #fafafa; }

.cell-business { font-weight: bold; max-width: 180px; }
.cell-email { color: #555; max-width: 160px; overflow: hidden; text-overflow: ellipsis; }
.cell-notes { color: #888; max-width: 200px; font-size: 0.78rem; }
.cell-actions { white-space: nowrap; }

.source-badge { padding: 2px 8px; font-size: 0.7rem; border-radius: 2px; }
.source-badge.manual { background: #f0f0f0; }
.source-badge.google_maps { background: #e8f0f8; color: #0055aa; }
.source-badge.linkedin_script { background: #e8f4e8; color: #005500; }

.stage-select { padding: 4px 8px; border: 1px solid #ddd; font-family: inherit; font-size: 0.78rem; background: #fff; cursor: pointer; }
.stage-select.replied   { border-color: #090; color: #090; }
.stage-select.closed    { border-color: #090; background: #e8f8e8; }
.stage-select.rejected  { border-color: #c00; color: #c00; }
.stage-select.booked    { border-color: #0055aa; color: #0055aa; }
.stage-select.email_sequence { border-color: #f60; color: #f60; }

.btn-chat { background: none; border: none; font-size: 1.1rem; cursor: pointer; padding: 4px 6px; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal { background: #fff; padding: 32px; max-width: 560px; width: 90%; font-family: 'Courier New', monospace; }
.modal h3 { margin-bottom: 12px; font-size: 1.1rem; }
.modal-hint { font-size: 0.82rem; color: #666; margin-bottom: 16px; line-height: 1.5; }
.csv-input { width: 100%; padding: 10px; border: 1px solid #ddd; font-family: inherit; font-size: 0.8rem; resize: vertical; }
.modal-actions { display: flex; gap: 10px; margin-top: 16px; }
.btn-primary { padding: 10px 20px; background: #111; color: #fff; border: 2px solid #111; font-family: inherit; cursor: pointer; }
.btn-ghost { padding: 10px 20px; background: transparent; border: 2px solid #ddd; font-family: inherit; cursor: pointer; }
</style>
