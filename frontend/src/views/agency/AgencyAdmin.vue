<template>
  <div class="agency-admin">
    <nav class="agency-nav">
      <router-link to="/agency" class="nav-brand">ContentAgency.ai</router-link>
      <div class="nav-links">
        <router-link to="/agency/portal">Portal</router-link>
        <span class="admin-badge">ADMIN</span>
      </div>
    </nav>

    <div class="admin-inner">
      <h1>Admin Dashboard</h1>

      <!-- Metrics -->
      <div v-if="metrics" class="metrics-grid">
        <div class="metric-card">
          <div class="metric-val">€{{ metrics.mrr_eur?.toLocaleString() }}</div>
          <div class="metric-label">Monthly Recurring Revenue</div>
        </div>
        <div class="metric-card">
          <div class="metric-val">{{ metrics.active_clients }}</div>
          <div class="metric-label">Active Clients</div>
        </div>
        <div class="metric-card">
          <div class="metric-val">{{ metrics.pilot_clients }}</div>
          <div class="metric-label">On Pilot (€500)</div>
        </div>
        <div class="metric-card">
          <div class="metric-val">{{ metrics.retainer_clients }}</div>
          <div class="metric-label">On Retainer (€1,500)</div>
        </div>
        <div class="metric-card">
          <div class="metric-val">{{ metrics.packages_generated }}</div>
          <div class="metric-label">Packages Generated</div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="admin-tabs">
        <button :class="['tab', { active: activeTab === 'clients' }]" @click="activeTab = 'clients'">Clients</button>
        <button :class="['tab', { active: activeTab === 'outreach' }]" @click="activeTab = 'outreach'">Outreach Campaigns</button>
      </div>

      <!-- Clients tab -->
      <div v-if="activeTab === 'clients'" class="clients-section">
        <div class="section-header">
          <h2>Clients</h2>
          <select v-model="clientFilter" class="filter-select">
            <option value="">All statuses</option>
            <option value="onboarding">Onboarding</option>
            <option value="active">Active</option>
            <option value="paused">Paused</option>
            <option value="churned">Churned</option>
          </select>
        </div>
        <div v-if="loadingClients" class="loading-inline">Loading…</div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>Business</th>
              <th>Type</th>
              <th>City</th>
              <th>Plan</th>
              <th>Status</th>
              <th>Joined</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in filteredClients" :key="c.id">
              <td><strong>{{ c.business_name }}</strong></td>
              <td>{{ c.business_type }}</td>
              <td>{{ c.city }}</td>
              <td><span class="badge" :class="c.plan">{{ c.plan }}</span></td>
              <td><span class="badge" :class="c.status">{{ c.status }}</span></td>
              <td>{{ formatDate(c.created_at) }}</td>
              <td class="actions-cell">
                <button class="action-btn" @click="generateForClient(c)">Generate</button>
                <button class="action-btn danger" @click="confirmDelete(c)">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Outreach tab -->
      <div v-if="activeTab === 'outreach'" class="outreach-section">
        <div class="section-header">
          <h2>Outreach Campaigns</h2>
          <button class="btn-primary" @click="showNewCampaign = true">+ New Campaign</button>
        </div>
        <div v-if="loadingCampaigns" class="loading-inline">Loading…</div>
        <div v-else-if="campaigns.length === 0" class="empty-msg">
          No campaigns yet. Create one to generate LinkedIn DM templates.
        </div>
        <div v-else class="campaigns-list">
          <div v-for="c in campaigns" :key="c.id" class="campaign-card"
               @click="openCampaign(c)">
            <div class="campaign-header">
              <strong>{{ c.name }}</strong>
              <span class="badge" :class="c.status">{{ c.status }}</span>
            </div>
            <div class="campaign-meta">{{ c.business_type }} · {{ c.target_city }}</div>
            <div class="campaign-funnel">
              <span>{{ c.metrics?.total || 0 }} leads</span>
              <span>→ {{ c.metrics?.connected || 0 }} connected</span>
              <span>→ {{ c.metrics?.replied || 0 }} replied</span>
              <span>→ <strong>{{ c.metrics?.closed || 0 }} closed</strong></span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- New Campaign Modal -->
    <div v-if="showNewCampaign" class="modal-overlay" @click.self="showNewCampaign = false">
      <div class="modal">
        <button class="modal-close" @click="showNewCampaign = false">×</button>
        <h3>Create Outreach Campaign</h3>
        <div class="form-group">
          <label>Campaign name</label>
          <input v-model="newCampaign.name" type="text" placeholder="e.g. Gyms Dublin Q2 2026" />
        </div>
        <div class="form-group">
          <label>Business type</label>
          <select v-model="newCampaign.business_type">
            <option value="gym">Gym</option>
            <option value="salon">Salon</option>
            <option value="restaurant">Restaurant</option>
            <option value="clinic">Clinic</option>
            <option value="real_estate">Real Estate</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div class="form-group">
          <label>Target city</label>
          <input v-model="newCampaign.target_city" type="text" placeholder="e.g. Dublin" />
        </div>
        <p class="form-hint">Claude will generate LinkedIn DM templates and a Loom script for this campaign.</p>
        <p v-if="campaignError" class="form-error">{{ campaignError }}</p>
        <button class="btn-primary" @click="createNewCampaign" :disabled="creatingCampaign">
          {{ creatingCampaign ? 'Generating templates…' : 'Create Campaign →' }}
        </button>
      </div>
    </div>

    <!-- Campaign detail modal -->
    <div v-if="selectedCampaign" class="modal-overlay" @click.self="selectedCampaign = null">
      <div class="modal campaign-detail-modal">
        <button class="modal-close" @click="selectedCampaign = null">×</button>
        <OutreachTemplates :campaign="selectedCampaign" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getDashboardMetrics, getClients, listCampaigns, createCampaign } from '../../api/agency.js'
import OutreachTemplates from '../../components/agency/OutreachTemplates.vue'
import { useRouter } from 'vue-router'

const router = useRouter()

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

const newCampaign = ref({ name: '', business_type: 'gym', target_city: '' })

const filteredClients = computed(() => {
  if (!clientFilter.value) return clients.value
  return clients.value.filter(c => c.status === clientFilter.value)
})

function formatDate(iso) {
  return iso ? new Date(iso).toLocaleDateString('en-IE', { day: 'numeric', month: 'short', year: 'numeric' }) : ''
}

function openCampaign(c) { selectedCampaign.value = c }

async function generateForClient(client) {
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

onMounted(async () => {
  const [m, c, camp] = await Promise.allSettled([
    getDashboardMetrics(),
    getClients(),
    listCampaigns(),
  ])
  if (m.status === 'fulfilled') metrics.value = m.value.data
  if (c.status === 'fulfilled') clients.value = c.value.data || []
  if (camp.status === 'fulfilled') campaigns.value = camp.value.data || []
  loadingClients.value = false
  loadingCampaigns.value = false
})
</script>

<style scoped>
.agency-admin { font-family: 'Courier New', monospace; background: #f9f9f9; min-height: 100vh; }
.agency-nav { display: flex; justify-content: space-between; align-items: center; padding: 20px 40px; border-bottom: 2px solid #111; background: #fff; position: sticky; top: 0; z-index: 100; }
.nav-brand { font-size: 1.2rem; font-weight: bold; text-decoration: none; color: #111; }
.nav-links { display: flex; align-items: center; gap: 16px; }
.nav-links a { color: #111; text-decoration: none; font-size: 0.9rem; }
.admin-badge { background: #111; color: #fff; padding: 4px 10px; font-size: 0.75rem; font-weight: bold; letter-spacing: 0.1em; }

.admin-inner { max-width: 1200px; margin: 0 auto; padding: 48px 24px; }
.admin-inner h1 { font-size: 2rem; margin-bottom: 32px; }

.metrics-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; margin-bottom: 48px; }
.metric-card { background: #fff; border: 2px solid #111; padding: 24px; text-align: center; }
.metric-val { font-size: 2rem; font-weight: bold; }
.metric-label { font-size: 0.8rem; color: #888; margin-top: 6px; }

.admin-tabs { display: flex; border-bottom: 2px solid #111; margin-bottom: 32px; }
.tab { padding: 12px 28px; border: none; background: transparent; cursor: pointer; font-family: inherit; font-size: 0.9rem; color: #888; border-bottom: 4px solid transparent; margin-bottom: -2px; }
.tab.active { color: #111; border-bottom-color: #111; font-weight: bold; }

.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.section-header h2 { font-size: 1.4rem; }
.filter-select { padding: 8px 12px; border: 2px solid #ddd; font-family: inherit; background: #fff; }
.loading-inline { color: #888; padding: 24px 0; }

.data-table { width: 100%; border-collapse: collapse; background: #fff; }
.data-table th { text-align: left; padding: 12px 16px; border-bottom: 2px solid #111; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; }
.data-table td { padding: 12px 16px; border-bottom: 1px solid #eee; font-size: 0.9rem; }
.data-table tr:hover td { background: #f9f9f9; }
.badge { display: inline-block; padding: 2px 8px; font-size: 0.75rem; border: 1px solid; }
.badge.active, .badge.completed { border-color: #090; color: #090; }
.badge.pilot { border-color: #999; color: #999; }
.badge.retainer { border-color: #09f; color: #09f; }
.badge.draft { border-color: #f90; color: #f90; }
.badge.onboarding { border-color: #f90; color: #f90; }
.badge.churned, .badge.paused { border-color: #c00; color: #c00; }
.actions-cell { display: flex; gap: 8px; }
.action-btn { padding: 6px 12px; border: 1px solid #ddd; background: #fff; font-family: inherit; font-size: 0.8rem; cursor: pointer; }
.action-btn:hover { background: #f0f0f0; }
.action-btn.danger { border-color: #c00; color: #c00; }
.action-btn.danger:hover { background: #fff0f0; }

.empty-msg { padding: 40px; text-align: center; color: #888; border: 2px dashed #ddd; background: #fff; }
.campaigns-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
.campaign-card { background: #fff; border: 2px solid #ddd; padding: 24px; cursor: pointer; }
.campaign-card:hover { border-color: #111; }
.campaign-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.campaign-meta { font-size: 0.85rem; color: #888; margin-bottom: 12px; }
.campaign-funnel { font-size: 0.82rem; display: flex; flex-wrap: wrap; gap: 8px; color: #555; }

.btn-primary { display: inline-block; background: #111; color: #fff; padding: 12px 24px; font-family: inherit; font-size: 0.9rem; font-weight: bold; border: 2px solid #111; cursor: pointer; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 24px; }
.modal { background: #fff; border: 2px solid #111; padding: 40px; width: 100%; max-width: 560px; position: relative; max-height: 90vh; overflow-y: auto; }
.campaign-detail-modal { max-width: 740px; }
.modal h3 { font-size: 1.3rem; margin-bottom: 24px; }
.modal-close { position: absolute; top: 16px; right: 16px; background: none; border: none; font-size: 1.5rem; cursor: pointer; }
.form-group { margin-bottom: 18px; }
.form-group label { display: block; font-size: 0.85rem; font-weight: bold; margin-bottom: 6px; }
.form-group input, .form-group select { width: 100%; padding: 10px; border: 2px solid #ccc; font-family: inherit; font-size: 0.9rem; box-sizing: border-box; }
.form-hint { font-size: 0.82rem; color: #888; margin-bottom: 16px; }
.form-error { color: #c00; font-size: 0.85rem; margin-bottom: 12px; }
</style>
