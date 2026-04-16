<template>
  <Transition name="slide">
    <div
      class="chat-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="chat-lead-name"
      @click.self="$emit('close')"
      @keydown.esc="$emit('close')"
    >
      <aside class="chat-panel cagency">
        <header class="panel-head">
          <div class="lead-info">
            <span class="ca-kicker">Lead</span>
            <strong id="chat-lead-name">{{ lead.first_name || 'Lead' }}</strong>
            <span class="biz">{{ lead.business_name }}</span>
            <span v-if="conversation" class="ca-pill on-dark" :class="stagePill(conversation.stage)">
              {{ conversation.stage }}
            </span>
          </div>
          <button class="close-btn" @click="$emit('close')" aria-label="Close conversation">×</button>
        </header>

        <div v-if="loading" class="panel-body center">
          <span class="spinner" aria-hidden="true"></span>
          <p>Loading conversation…</p>
        </div>

        <div v-else-if="!conversation" class="panel-body center">
          <p class="no-conv">No conversation started yet.</p>
          <button class="ca-btn" @click="startConv" :disabled="starting">
            {{ starting ? 'Starting…' : 'Start AI conversation' }}
          </button>
        </div>

        <div v-else class="panel-body" ref="scrollEl">
          <div
            v-for="(msg, i) in conversation.messages"
            :key="i"
            class="msg"
            :class="msg.role"
          >
            <div class="msg-role">
              {{ msg.role === 'assistant' ? 'AI · ContentAgency' : 'Lead' }}
            </div>
            <div class="msg-content">{{ msg.content }}</div>
            <div class="msg-time">{{ formatTime(msg.timestamp) }}</div>
          </div>
        </div>

        <footer
          v-if="conversation && conversation.stage !== 'won' && conversation.stage !== 'lost'"
          class="panel-footer"
        >
          <span class="ca-kicker">Simulate inbound reply</span>
          <div class="reply-row">
            <textarea
              v-model="replyText"
              rows="3"
              class="reply-input"
              placeholder="Paste or type the lead's reply…"
              @keydown.ctrl.enter="sendReply"
              aria-label="Lead reply text"
            ></textarea>
            <button
              class="ca-btn"
              @click="sendReply"
              :disabled="sending || !replyText.trim()"
            >{{ sending ? '…' : 'Send' }}</button>
          </div>
        </footer>
        <footer v-else-if="conversation" class="panel-footer">
          <div class="stage-final" :class="conversation.stage">
            Conversation {{ conversation.stage === 'won' ? 'won' : 'lost' }}
          </div>
        </footer>
      </aside>
    </div>
  </Transition>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { startConversation, listConversations, getConversation, injectReply } from '../../api/agency.js'

const props = defineProps({ lead: { type: Object, required: true } })
defineEmits(['close'])

const loading      = ref(true)
const starting     = ref(false)
const sending      = ref(false)
const conversation = ref(null)
const replyText    = ref('')
const scrollEl     = ref(null)

onMounted(async () => {
  try {
    const res = await listConversations(props.lead.id)
    const convs = res.data.data || []
    if (convs.length) {
      const full = await getConversation(convs[0].id)
      conversation.value = full.data.data
    }
  } catch {/* no conversation yet */} finally {
    loading.value = false
    await nextTick()
    scrollToBottom()
  }
})

watch(conversation, async () => {
  await nextTick()
  scrollToBottom()
}, { deep: true })

async function startConv() {
  starting.value = true
  try {
    await startConversation(props.lead.id)
    const res  = await listConversations(props.lead.id)
    const convs = res.data.data || []
    if (convs.length) {
      const full = await getConversation(convs[0].id)
      conversation.value = full.data.data
    }
  } catch (e) {
    alert(e?.response?.data?.error || 'Failed to start conversation')
  } finally {
    starting.value = false
  }
}

async function sendReply() {
  if (!replyText.value.trim() || !conversation.value) return
  sending.value = true
  try {
    await injectReply(conversation.value.id, replyText.value.trim())
    replyText.value = ''
    const full = await getConversation(conversation.value.id)
    conversation.value = full.data.data
  } catch (e) {
    alert(e?.response?.data?.error || 'Failed to send reply')
  } finally {
    sending.value = false
  }
}

function scrollToBottom() {
  if (scrollEl.value) {
    scrollEl.value.scrollTop = scrollEl.value.scrollHeight
  }
}

function formatTime(iso) {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleTimeString('en-IE', { hour: '2-digit', minute: '2-digit' })
  } catch { return iso }
}

function stagePill(stage) {
  return {
    won: 'ok',
    lost: 'err',
    closing: 'brand',
  }[stage] || ''
}
</script>

<style scoped>
.chat-overlay {
  position: fixed; inset: 0;
  background: color-mix(in oklab, var(--void, #000), transparent 55%);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  display: flex; justify-content: flex-end;
  z-index: 2000;
}
.chat-panel {
  width: 480px; max-width: 100%;
  background: var(--paper);
  display: flex; flex-direction: column;
  box-shadow: -16px 0 48px -16px oklch(0.15 0.02 270 / 0.25);
  height: 100%;
}

.panel-head {
  display: flex; justify-content: space-between; align-items: flex-start;
  padding: var(--s-5);
  background: var(--void);
  color: var(--moon);
  border-bottom: 1px solid color-mix(in oklab, var(--moon), transparent 88%);
}
.lead-info { display: flex; flex-direction: column; gap: 6px; }
.lead-info .ca-kicker { color: var(--moon-mute); }
.lead-info strong {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 1.125rem;
  letter-spacing: -0.02em;
  color: var(--moon);
}
.biz {
  font-size: var(--caption);
  color: var(--moon-soft);
  font-family: var(--font-mono);
  letter-spacing: 0.03em;
}

.close-btn {
  background: transparent;
  border: 1px solid color-mix(in oklab, var(--moon), transparent 75%);
  color: var(--moon);
  width: 32px; height: 32px;
  border-radius: var(--r-full);
  font-size: 1.2rem; line-height: 1;
  cursor: pointer;
  transition: background var(--dur-2) var(--ease-out);
}
.close-btn:hover { background: color-mix(in oklab, var(--moon), transparent 88%); }
.close-btn:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--s-5);
  display: flex; flex-direction: column; gap: var(--s-3);
  background: var(--surface-1);
}
.panel-body.center {
  justify-content: center; align-items: center; text-align: center;
  gap: var(--s-3);
}
.no-conv { color: var(--ink-lo); font-size: var(--small); }
.spinner {
  width: 26px; height: 26px;
  border: 2px solid color-mix(in oklab, var(--ink-hi), transparent 88%);
  border-top-color: var(--ink-hi);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.msg {
  border: 1px solid var(--hairline);
  border-radius: var(--r-3);
  padding: var(--s-3) var(--s-4);
  background: var(--paper);
  box-shadow: var(--shadow-sm);
}
.msg.assistant {
  background: var(--brand-wash);
  border-color: color-mix(in oklab, var(--brand), transparent 80%);
}
.msg.user {
  background: var(--flame-wash);
  border-color: color-mix(in oklab, var(--flame), transparent 75%);
}
.msg-role {
  font-family: var(--font-mono);
  font-size: var(--mono-cap);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--ink-lo);
  margin-bottom: 4px;
}
.msg.assistant .msg-role { color: var(--brand); }
.msg.user .msg-role { color: oklch(0.45 0.15 75); }
.msg-content {
  font-size: var(--small);
  line-height: 1.65;
  white-space: pre-wrap;
  color: var(--ink-hi);
}
.msg-time {
  font-family: var(--font-mono);
  font-size: 0.68rem;
  color: var(--ink-lo);
  margin-top: 6px;
  text-align: right;
  letter-spacing: 0.03em;
}

.panel-footer {
  padding: var(--s-4) var(--s-5);
  border-top: 1px solid var(--hairline);
  background: var(--paper);
}
.panel-footer .ca-kicker { margin-bottom: var(--s-2); display: flex; }

.reply-row { display: flex; gap: var(--s-2); align-items: flex-end; }
.reply-input {
  flex: 1;
  padding: var(--s-3);
  border: 1px solid var(--hairline);
  border-radius: var(--r-2);
  font: inherit; font-size: var(--small);
  background: var(--surface-1);
  color: var(--ink-hi);
  resize: none;
  transition: border-color var(--dur-2) var(--ease-out),
              box-shadow var(--dur-2) var(--ease-out);
}
.reply-input:focus {
  outline: none;
  border-color: var(--brand);
  background: var(--paper);
  box-shadow: 0 0 0 4px color-mix(in oklab, var(--brand), transparent 88%);
}

.stage-final {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 0.95rem;
  letter-spacing: -0.015em;
  text-align: center;
  padding: var(--s-3);
  border-radius: var(--r-2);
}
.stage-final.won  { color: var(--ok);  background: color-mix(in oklab, var(--ok),  var(--paper) 88%); }
.stage-final.lost { color: var(--err); background: color-mix(in oklab, var(--err), var(--paper) 90%); }

.slide-enter-active, .slide-leave-active {
  transition: opacity var(--dur-3) var(--ease-out);
}
.slide-enter-active .chat-panel, .slide-leave-active .chat-panel {
  transition: transform var(--dur-4) var(--ease-out);
}
.slide-enter-from, .slide-leave-to { opacity: 0; }
.slide-enter-from .chat-panel, .slide-leave-to .chat-panel {
  transform: translateX(100%);
}
</style>
