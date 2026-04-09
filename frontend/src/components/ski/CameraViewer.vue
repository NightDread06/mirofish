<template>
  <div class="camera-viewer">
    <div class="panel-header">
      <span class="panel-title">📷 Live Webcams</span>
      <div class="cam-controls">
        <button class="ctrl-btn" @click="prev">‹</button>
        <span class="cam-counter">{{ activeCam + 1 }} / {{ cameras.length }}</span>
        <button class="ctrl-btn" @click="next">›</button>
        <button class="ctrl-btn" :class="{ active: autoRotate }" @click="toggleAuto" title="Auto-rotate">
          ⟳
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading webcams…</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <template v-else-if="cameras.length">
      <!-- Main camera display -->
      <div class="cam-main">
        <div class="cam-status-bar">
          <span class="cam-name">{{ current.name }}</span>
          <span class="status-badge" :class="'status-' + current.status">
            {{ current.status }}
          </span>
        </div>

        <a :href="current.url" target="_blank" rel="noopener" class="cam-link">
          <div class="cam-frame" :class="{ 'cam-offline': current.status === 'offline' }">
            <img
              v-if="current.thumbnail"
              :src="current.thumbnail"
              :alt="current.name"
              class="cam-img"
              @error="imgError"
            />
            <div v-else class="cam-placeholder">
              <div class="cam-icon">📷</div>
              <div class="cam-loc">{{ current.location }}</div>
              <div class="cam-open-hint">Click to open webcam ↗</div>
            </div>

            <div v-if="current.status === 'offline'" class="offline-overlay">
              <span>OFFLINE</span>
            </div>
          </div>
        </a>

        <div class="cam-meta">
          📍 {{ current.location }}
          <span v-if="lastUpdated" class="cam-updated">· Updated {{ lastUpdated }}</span>
        </div>
      </div>

      <!-- Thumbnail strip -->
      <div class="cam-strip">
        <button
          v-for="(cam, idx) in cameras"
          :key="cam.id"
          class="strip-item"
          :class="{ active: idx === activeCam }"
          @click="activeCam = idx; resetAuto()"
        >
          <span class="strip-dot" :class="'status-' + cam.status"></span>
          <span class="strip-name">{{ cam.name }}</span>
        </button>
      </div>
    </template>

    <div v-else class="empty">No cameras configured.</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getCameras } from '../../api/ski.js'

const cameras = ref([])
const loading = ref(true)
const error = ref(null)
const activeCam = ref(0)
const autoRotate = ref(false)
const lastUpdated = ref(null)

const REFRESH_MS = 10 * 60 * 1000
const AUTO_INTERVAL_MS = 8000

const current = computed(() => cameras.value[activeCam.value] || {})

function prev() {
  activeCam.value = (activeCam.value - 1 + cameras.value.length) % cameras.value.length
  resetAuto()
}

function next() {
  activeCam.value = (activeCam.value + 1) % cameras.value.length
  resetAuto()
}

let autoTimer = null
function toggleAuto() {
  autoRotate.value = !autoRotate.value
  if (autoRotate.value) {
    autoTimer = setInterval(() => {
      activeCam.value = (activeCam.value + 1) % cameras.value.length
    }, AUTO_INTERVAL_MS)
  } else {
    clearInterval(autoTimer)
  }
}

function resetAuto() {
  if (autoRotate.value) {
    clearInterval(autoTimer)
    autoTimer = setInterval(() => {
      activeCam.value = (activeCam.value + 1) % cameras.value.length
    }, AUTO_INTERVAL_MS)
  }
}

function imgError(e) {
  e.target.style.display = 'none'
}

async function load() {
  loading.value = true
  error.value = null
  try {
    const data = await getCameras()
    cameras.value = data.cameras || []
    lastUpdated.value = data.timestamp
      ? new Date(data.timestamp).toLocaleTimeString()
      : null
  } catch (e) {
    error.value = 'Could not load webcam list.'
  } finally {
    loading.value = false
  }
}

let refreshTimer = null
onMounted(() => {
  load()
  refreshTimer = setInterval(load, REFRESH_MS)
})
onUnmounted(() => {
  clearInterval(refreshTimer)
  clearInterval(autoTimer)
})

defineExpose({ refresh: load })
</script>

<style scoped>
.camera-viewer {
  background: #fff;
  border: 1px solid #e5e5e5;
  padding: 20px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.panel-title { font-weight: 700; font-size: 1rem; }

.cam-controls {
  display: flex;
  align-items: center;
  gap: 6px;
}

.ctrl-btn {
  background: transparent;
  border: 1px solid #ddd;
  padding: 4px 10px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.2s;
}
.ctrl-btn:hover, .ctrl-btn.active { background: #000; color: #fff; border-color: #000; }

.cam-counter { font-size: 0.8rem; color: #999; min-width: 40px; text-align: center; }

.loading, .error, .empty {
  padding: 20px 0;
  font-size: 0.9rem;
  color: #999;
}
.error { color: #e53e3e; }

.cam-main { margin-bottom: 12px; }

.cam-status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.cam-name { font-weight: 600; font-size: 0.95rem; }

.status-badge {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 10px;
  text-transform: uppercase;
}
.status-online  { background: #c6f6d5; color: #22543d; }
.status-offline { background: #fed7d7; color: #742a2a; }

.cam-link { display: block; text-decoration: none; }

.cam-frame {
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #111;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cam-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cam-placeholder {
  text-align: center;
  color: #666;
}

.cam-icon { font-size: 2.5rem; margin-bottom: 8px; }
.cam-loc  { font-size: 0.85rem; color: #999; }
.cam-open-hint { font-size: 0.75rem; color: #555; margin-top: 6px; }

.offline-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  letter-spacing: 2px;
  font-size: 1.1rem;
}

.cam-meta {
  margin-top: 8px;
  font-size: 0.78rem;
  color: #aaa;
}

.cam-updated { margin-left: 4px; }

/* Thumbnail strip */
.cam-strip {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  border-top: 1px solid #f0f0f0;
  padding-top: 12px;
}

.strip-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  border: 1px solid #eee;
  background: #fafafa;
  cursor: pointer;
  font-size: 0.78rem;
  transition: all 0.2s;
}
.strip-item:hover, .strip-item.active {
  border-color: #000;
  background: #000;
  color: #fff;
}

.strip-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.strip-dot.status-online  { background: #48bb78; }
.strip-dot.status-offline { background: #fc8181; }

.strip-name { font-size: 0.75rem; }
</style>
