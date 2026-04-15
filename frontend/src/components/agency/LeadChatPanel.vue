<template>
  <div class="chat-overlay" @click.self="$emit('close')">
    <div class="chat-panel">
      <!-- Header -->
      <div class="panel-header">
        <div class="lead-info">
          <strong>{{ lead.first_name || 'Lead' }}</strong>
          <span class="biz">{{ lead.business_name }}</span>
          <span v-if="conversation" class="stage-pill" :class="conversation.stage">
            {{ conversation.stage }}
          </span>
        </div>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="panel-body center">Loading conversation…</div>

      <!-- No conversation yet -->
      <div v-else-if="!conversation" class="panel-body center">
        <p class="no-conv">No conversation started yet.</p>
        <button class="btn-start" @click="startConv" :disabled="starting">
          {{ starting ? 'Starting…' : 'Start AI Conversation' }}
        </button>
      </div>

      <!-- Conversation thread -->
      <div v-else class="panel-body" ref="scrollEl">
        <div
          v-for="(msg, i) in conversation.messages"
          :key="i"
          class="message"
          :class="msg.role"
        >
          <div class="msg-role">{{ msg.role === 'assistant' ? 'AI (ContentAgency.ai)' : 'Lead' }}</div>
          <div class="msg-content">{{ msg.content }}</div>
          <div class="msg-time">{{ formatTime(msg.timestamp) }}</div>
        </div>
      </div>

      <!-- Manual reply input (for testing / manual trigger) -->
      <div v-if="conversation && conversation.stage !== 'won' && conversation.stage !== 'lost'"
           class="panel-footer">
        <div class="footer-label">Simulate inbound reply (test mode):</div>
        <div class="reply-row">
          <textarea v-model="replyText" rows="3" class="reply-input"
            placeholder="Paste or type the lead's reply…"
            @keydown.ctrl.enter="sendReply"></textarea>
          <button class="btn-send" @click="sendReply" :disabled="sending || !replyText.trim()">
            {{ sending ? '…' : 'Send' }}
          </button>
        </div>
      </div>
      <div v-else-if="conversation" class="panel-footer">
        <div class="footer-label stage-final" :class="conversation.stage">
          Conversation {{ conversation.stage === 'won' ? '✓ Won' : '✗ Lost' }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { startConversation, listConversations, getConversation, injectReply } from '../../api/agency.js'

const props = defineProps({ lead: { type: Object, required: true } })
const emit  = defineEmits(['close'])

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
</script>

<style scoped>
.chat-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.4);
  display: flex; justify-content: flex-end; z-index: 2000;
}
.chat-panel {
  width: 480px; max-width: 100%;
  background: #fff; display: flex; flex-direction: column;
  font-family: 'Courier New', monospace;
  box-shadow: -4px 0 24px rgba(0,0,0,0.15);
}

.panel-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; border-bottom: 2px solid #111;
  background: #111; color: #fff;
}
.lead-info { display: flex; flex-direction: column; gap: 3px; }
.lead-info strong { font-size: 1rem; }
.biz { font-size: 0.8rem; color: #ccc; }
.stage-pill {
  display: inline-block; padding: 2px 8px; font-size: 0.7rem; border-radius: 2px;
  background: #333; color: #fff; width: fit-content;
}
.stage-pill.won  { background: #090; }
.stage-pill.lost { background: #c00; }
.stage-pill.closing  { background: #0055aa; }
.close-btn { background: none; border: none; color: #fff; font-size: 1.2rem; cursor: pointer; }

.panel-body {
  flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 16px;
}
.panel-body.center { justify-content: center; align-items: center; text-align: center; }
.no-conv { color: #888; margin-bottom: 16px; font-size: 0.9rem; }
.btn-start {
  padding: 10px 24px; background: #111; color: #fff;
  border: none; cursor: pointer; font-family: inherit; font-size: 0.9rem;
}
.btn-start:disabled { background: #888; cursor: not-allowed; }

.message { border: 1px solid #eee; padding: 12px 14px; }
.message.assistant { background: #f9f9f9; }
.message.user { background: #fffbe8; border-color: #f0c040; }
.msg-role { font-size: 0.7rem; font-weight: bold; text-transform: uppercase; color: #888; margin-bottom: 6px; }
.message.assistant .msg-role { color: #0055aa; }
.message.user .msg-role { color: #b85c00; }
.msg-content { font-size: 0.88rem; line-height: 1.6; white-space: pre-wrap; }
.msg-time { font-size: 0.68rem; color: #bbb; margin-top: 6px; text-align: right; }

.panel-footer {
  padding: 16px 20px; border-top: 1px solid #eee; background: #fafafa;
}
.footer-label { font-size: 0.72rem; color: #888; margin-bottom: 8px; }
.stage-final { font-weight: bold; font-size: 0.85rem; }
.stage-final.won  { color: #090; }
.stage-final.lost { color: #c00; }
.reply-row { display: flex; gap: 8px; align-items: flex-end; }
.reply-input {
  flex: 1; padding: 8px 10px; border: 1px solid #ddd;
  font-family: inherit; font-size: 0.82rem; resize: none;
}
.btn-send {
  padding: 8px 16px; background: #111; color: #fff;
  border: none; cursor: pointer; font-family: inherit; white-space: nowrap;
}
.btn-send:disabled { background: #999; cursor: not-allowed; }
</style>
