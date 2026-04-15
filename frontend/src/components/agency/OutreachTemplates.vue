<template>
  <div class="outreach-templates">
    <h2>{{ campaign.name }}</h2>
    <div class="campaign-info">
      <span class="info-tag">{{ campaign.business_type }}</span>
      <span class="info-tag">{{ campaign.target_city }}</span>
      <span class="badge" :class="campaign.status">{{ campaign.status }}</span>
    </div>

    <!-- Funnel metrics -->
    <div class="funnel-bar">
      <div class="funnel-step" v-for="step in funnelSteps" :key="step.key">
        <div class="funnel-val">{{ campaign.metrics?.[step.key] || 0 }}</div>
        <div class="funnel-label">{{ step.label }}</div>
      </div>
      <div class="funnel-conversion" v-if="campaign.metrics?.total > 0">
        Close rate: {{ closeRate }}%
      </div>
    </div>

    <div v-if="!campaign.templates?.connection_msg" class="no-templates">
      <p>Templates are being generated… Refresh in a moment.</p>
    </div>

    <template v-else>
      <!-- Template tabs -->
      <div class="template-tabs">
        <button v-for="t in templateTabs" :key="t.key"
                :class="['tab', { active: activeTemplate === t.key }]"
                @click="activeTemplate = t.key">
          {{ t.label }}
        </button>
      </div>

      <!-- Connection request -->
      <div v-if="activeTemplate === 'connection'" class="template-block">
        <div class="template-header">
          <span>LinkedIn Connection Note</span>
          <span class="char-count" :class="{ warning: connectionLength > 250 }">
            {{ connectionLength }}/300 chars
          </span>
          <button class="copy-btn" @click="copyTemplate('connection', campaign.templates.connection_msg)">
            {{ copied === 'connection' ? 'Copied!' : 'Copy' }}
          </button>
        </div>
        <div class="template-text">{{ campaign.templates.connection_msg }}</div>
      </div>

      <!-- DM sequence -->
      <div v-if="activeTemplate === 'dm1'" class="template-block">
        <div class="template-header">
          <span>Initial DM (after connecting)</span>
          <button class="copy-btn" @click="copyTemplate('dm1', campaign.templates.dm_1)">
            {{ copied === 'dm1' ? 'Copied!' : 'Copy' }}
          </button>
        </div>
        <div class="template-text">{{ campaign.templates.dm_1 }}</div>
      </div>

      <div v-if="activeTemplate === 'dm2'" class="template-block">
        <div class="template-header">
          <span>Follow-up #1 — Day 3 (if no reply)</span>
          <button class="copy-btn" @click="copyTemplate('dm2', campaign.templates.dm_2)">
            {{ copied === 'dm2' ? 'Copied!' : 'Copy' }}
          </button>
        </div>
        <div class="template-text">{{ campaign.templates.dm_2 }}</div>
      </div>

      <div v-if="activeTemplate === 'dm3'" class="template-block">
        <div class="template-header">
          <span>Follow-up #2 — Day 7 (value-add close)</span>
          <button class="copy-btn" @click="copyTemplate('dm3', campaign.templates.dm_3)">
            {{ copied === 'dm3' ? 'Copied!' : 'Copy' }}
          </button>
        </div>
        <div class="template-text">{{ campaign.templates.dm_3 }}</div>
      </div>

      <!-- Loom script -->
      <div v-if="activeTemplate === 'loom'" class="template-block">
        <div class="template-header">
          <span>60-Second Loom Video Script</span>
          <button class="copy-btn" @click="copyTemplate('loom', campaign.templates.loom_script)">
            {{ copied === 'loom' ? 'Copied!' : 'Copy' }}
          </button>
        </div>
        <div class="template-text loom-script">{{ campaign.templates.loom_script }}</div>
        <p class="loom-tip">Record at <strong>loom.com</strong> — screen share their website/social while reading this script.</p>
      </div>
    </template>

    <!-- Tips -->
    <div class="outreach-tips">
      <h3>Outreach Tips</h3>
      <ul>
        <li>Send 20–30 connection requests per day (LinkedIn limits ~100/week)</li>
        <li>Personalise the opener with a specific observation about their business</li>
        <li>Send DM #1 within 24h of connecting — while you're top of mind</li>
        <li>Record Loom videos only for people who respond (saves time, increases quality)</li>
        <li>Track every lead stage using the Leads tab in your campaign</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useClipboard } from '@vueuse/core'

const props = defineProps({
  campaign: { type: Object, required: true },
})

const { copy } = useClipboard()
const copied = ref('')
const activeTemplate = ref('connection')

const templateTabs = [
  { key: 'connection', label: 'Connection Note' },
  { key: 'dm1',        label: 'DM #1' },
  { key: 'dm2',        label: 'Follow-up #1' },
  { key: 'dm3',        label: 'Follow-up #2' },
  { key: 'loom',       label: 'Loom Script' },
]

const funnelSteps = [
  { key: 'total',     label: 'Leads' },
  { key: 'connected', label: 'Connected' },
  { key: 'replied',   label: 'Replied' },
  { key: 'booked',    label: 'Booked' },
  { key: 'closed',    label: 'Closed' },
]

const connectionLength = computed(() =>
  props.campaign.templates?.connection_msg?.length || 0
)

const closeRate = computed(() => {
  const { total, closed } = props.campaign.metrics || {}
  if (!total) return 0
  return ((closed / total) * 100).toFixed(1)
})

async function copyTemplate(key, text) {
  if (!text) return
  await copy(text)
  copied.value = key
  setTimeout(() => { copied.value = '' }, 2000)
}
</script>

<style scoped>
.outreach-templates { font-family: 'Courier New', monospace; }
h2 { font-size: 1.5rem; margin-bottom: 8px; }
.campaign-info { display: flex; gap: 8px; align-items: center; margin-bottom: 20px; flex-wrap: wrap; }
.info-tag { background: #f0f0f0; padding: 3px 10px; font-size: 0.8rem; }
.badge { padding: 3px 10px; font-size: 0.78rem; border: 1px solid; }
.badge.active { border-color: #090; color: #090; }
.badge.draft  { border-color: #f90; color: #f90; }

.funnel-bar { display: flex; flex-wrap: wrap; gap: 16px; align-items: center; margin-bottom: 24px; padding: 16px; background: #f9f9f9; border: 1px solid #eee; }
.funnel-step { text-align: center; }
.funnel-val { font-size: 1.4rem; font-weight: bold; }
.funnel-label { font-size: 0.72rem; color: #888; text-transform: uppercase; }
.funnel-conversion { font-size: 0.82rem; font-weight: bold; margin-left: auto; }

.no-templates { padding: 24px; text-align: center; color: #888; border: 2px dashed #ddd; }

.template-tabs { display: flex; flex-wrap: wrap; gap: 0; border-bottom: 2px solid #111; margin-bottom: 24px; }
.tab { padding: 10px 18px; border: none; background: transparent; cursor: pointer; font-family: inherit; font-size: 0.85rem; color: #888; border-bottom: 4px solid transparent; margin-bottom: -2px; }
.tab.active { color: #111; border-bottom-color: #111; font-weight: bold; }

.template-block { border: 2px solid #eee; padding: 24px; }
.template-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; font-size: 0.85rem; font-weight: bold; flex-wrap: wrap; }
.char-count { font-size: 0.78rem; color: #888; font-weight: normal; }
.char-count.warning { color: #c00; }
.copy-btn { margin-left: auto; padding: 4px 12px; border: 1px solid #ddd; background: #fff; font-family: inherit; font-size: 0.78rem; cursor: pointer; }
.copy-btn:hover { background: #f0f0f0; }

.template-text { white-space: pre-wrap; line-height: 1.7; font-size: 0.9rem; color: #333; }
.loom-script { background: #f9f9f9; padding: 16px; }
.loom-tip { margin-top: 12px; font-size: 0.82rem; color: #888; font-style: italic; }

.outreach-tips { margin-top: 28px; background: #f9f9f9; border: 1px solid #eee; padding: 20px; }
.outreach-tips h3 { font-size: 1rem; margin-bottom: 12px; }
.outreach-tips ul { padding-left: 20px; }
.outreach-tips li { font-size: 0.88rem; margin-bottom: 8px; line-height: 1.5; color: #555; }
</style>
