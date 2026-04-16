<template>
  <div class="outreach">
    <header class="ot-head">
      <span class="ca-kicker">Outreach</span>
      <h2>{{ campaign.name }}</h2>
      <div class="ot-meta">
        <span class="ca-pill">{{ campaign.business_type }}</span>
        <span class="ca-pill">{{ campaign.target_city }}</span>
        <span class="ca-pill" :class="statusPill(campaign.status)">
          {{ campaign.status }}
        </span>
      </div>
    </header>

    <div class="funnel">
      <div class="funnel-step" v-for="(step, i) in funnelSteps" :key="step.key">
        <span class="step-num">{{ campaign.metrics?.[step.key] || 0 }}</span>
        <span class="step-lbl">{{ step.label }}</span>
        <span v-if="i < funnelSteps.length - 1" class="step-arrow" aria-hidden="true">→</span>
      </div>
      <div class="funnel-conv" v-if="campaign.metrics?.total > 0">
        <span class="ca-kicker">Close rate</span>
        <strong>{{ closeRate }}%</strong>
      </div>
    </div>

    <div v-if="!campaign.templates?.connection_msg" class="empty-templates">
      <p>Templates are being generated. Refresh in a moment.</p>
    </div>

    <template v-else>
      <div class="tabs" role="tablist">
        <button
          v-for="t in templateTabs"
          :key="t.key"
          :class="['tab', { active: activeTemplate === t.key }]"
          role="tab"
          :aria-selected="activeTemplate === t.key"
          @click="activeTemplate = t.key"
        >{{ t.label }}</button>
      </div>

      <div v-if="activeTemplate === 'connection'" class="t-block">
        <div class="t-head">
          <span class="t-title">LinkedIn connection note</span>
          <span class="char-count" :class="{ warn: connectionLength > 250 }">
            {{ connectionLength }}/300
          </span>
          <button
            class="copy-btn"
            @click="copyTemplate('connection', campaign.templates.connection_msg)"
          >{{ copied === 'connection' ? 'Copied' : 'Copy' }}</button>
        </div>
        <pre class="t-text">{{ campaign.templates.connection_msg }}</pre>
      </div>

      <div v-if="activeTemplate === 'dm1'" class="t-block">
        <div class="t-head">
          <span class="t-title">Initial DM (after connecting)</span>
          <button class="copy-btn" @click="copyTemplate('dm1', campaign.templates.dm_1)">
            {{ copied === 'dm1' ? 'Copied' : 'Copy' }}
          </button>
        </div>
        <pre class="t-text">{{ campaign.templates.dm_1 }}</pre>
      </div>

      <div v-if="activeTemplate === 'dm2'" class="t-block">
        <div class="t-head">
          <span class="t-title">Follow-up #1 — day 3</span>
          <button class="copy-btn" @click="copyTemplate('dm2', campaign.templates.dm_2)">
            {{ copied === 'dm2' ? 'Copied' : 'Copy' }}
          </button>
        </div>
        <pre class="t-text">{{ campaign.templates.dm_2 }}</pre>
      </div>

      <div v-if="activeTemplate === 'dm3'" class="t-block">
        <div class="t-head">
          <span class="t-title">Follow-up #2 — day 7 (value-add close)</span>
          <button class="copy-btn" @click="copyTemplate('dm3', campaign.templates.dm_3)">
            {{ copied === 'dm3' ? 'Copied' : 'Copy' }}
          </button>
        </div>
        <pre class="t-text">{{ campaign.templates.dm_3 }}</pre>
      </div>

      <div v-if="activeTemplate === 'loom'" class="t-block">
        <div class="t-head">
          <span class="t-title">60-second Loom script</span>
          <button class="copy-btn" @click="copyTemplate('loom', campaign.templates.loom_script)">
            {{ copied === 'loom' ? 'Copied' : 'Copy' }}
          </button>
        </div>
        <pre class="t-text loom">{{ campaign.templates.loom_script }}</pre>
        <p class="loom-tip">
          Record at <strong>loom.com</strong> — screen share their website
          or social while reading this script.
        </p>
      </div>
    </template>

    <aside class="tips">
      <span class="ca-kicker">Outreach playbook</span>
      <ul>
        <li>Send 20–30 connection requests per day (LinkedIn limits ~100/week).</li>
        <li>Personalise the opener with a specific observation about their business.</li>
        <li>Send DM #1 within 24h of connecting — while you're top of mind.</li>
        <li>Record Loom only for people who respond — saves time, increases quality.</li>
        <li>Track every lead stage in the Leads tab of your campaign.</li>
      </ul>
    </aside>
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
  { key: 'connection', label: 'Connection' },
  { key: 'dm1',        label: 'DM #1' },
  { key: 'dm2',        label: 'Follow-up #1' },
  { key: 'dm3',        label: 'Follow-up #2' },
  { key: 'loom',       label: 'Loom script' },
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

function statusPill(s) {
  return { active: 'ok', draft: 'warn', paused: 'err' }[s] || ''
}

async function copyTemplate(key, text) {
  if (!text) return
  await copy(text)
  copied.value = key
  setTimeout(() => { copied.value = '' }, 2000)
}
</script>

<style scoped>
.outreach { font-family: var(--font-body); color: var(--ink); }

.ot-head { margin-bottom: var(--s-5); }
.ot-head h2 {
  font-family: var(--font-display); font-weight: 600;
  font-size: 1.75rem; letter-spacing: -0.02em;
  color: var(--ink-hi);
  margin: var(--s-2) 0 var(--s-3);
}
.ot-meta { display: flex; flex-wrap: wrap; gap: var(--s-2); }

.funnel {
  display: flex; flex-wrap: wrap; align-items: center;
  gap: var(--s-4);
  padding: var(--s-5);
  border: 1px solid var(--hairline);
  border-radius: var(--r-3);
  background: var(--surface-1);
  margin-bottom: var(--s-6);
}
.funnel-step {
  display: flex; align-items: center; gap: var(--s-3);
}
.step-num {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 1.375rem;
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
.funnel-conv {
  margin-left: auto;
  display: flex; flex-direction: column; align-items: flex-end; gap: 2px;
  font-size: var(--body-lg);
  color: var(--ink-hi);
}
.funnel-conv strong {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 1.25rem;
  letter-spacing: -0.02em;
}

.empty-templates {
  padding: var(--s-6);
  text-align: center;
  color: var(--ink-lo);
  border: 1px dashed var(--hairline-2);
  border-radius: var(--r-3);
  background: var(--surface-1);
}

.tabs {
  display: flex; flex-wrap: wrap;
  border-bottom: 1px solid var(--hairline);
  margin-bottom: var(--s-5);
}
.tab {
  padding: 10px 16px;
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
.tab:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }

.t-block {
  border: 1px solid var(--hairline);
  border-radius: var(--r-3);
  padding: var(--s-5);
  background: var(--paper);
}
.t-head {
  display: flex; align-items: center; gap: var(--s-3);
  margin-bottom: var(--s-4);
  padding-bottom: var(--s-3);
  border-bottom: 1px solid var(--hairline);
  flex-wrap: wrap;
}
.t-title {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 1rem;
  letter-spacing: -0.015em;
  color: var(--ink-hi);
}
.char-count {
  font-family: var(--font-mono);
  font-size: var(--mono-cap);
  color: var(--ink-lo);
  letter-spacing: 0.05em;
}
.char-count.warn { color: var(--err); }
.copy-btn {
  margin-left: auto;
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
.copy-btn:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }

.t-text {
  font-family: var(--font-body);
  white-space: pre-wrap;
  line-height: 1.7;
  font-size: var(--body);
  color: var(--ink-hi);
  margin: 0;
  max-width: var(--measure);
}
.t-text.loom {
  background: var(--surface-2);
  padding: var(--s-4);
  border-radius: var(--r-2);
}
.loom-tip {
  margin-top: var(--s-3);
  font-size: var(--small);
  color: var(--ink-lo);
  font-style: italic;
}

.tips {
  margin-top: var(--s-6);
  padding: var(--s-5);
  background: var(--brand-wash);
  border: 1px solid color-mix(in oklab, var(--brand), transparent 85%);
  border-radius: var(--r-3);
}
.tips ul { margin: var(--s-3) 0 0; padding-left: var(--s-5); }
.tips li {
  font-size: var(--small);
  color: var(--ink);
  line-height: 1.6;
  margin-bottom: var(--s-2);
}
</style>
