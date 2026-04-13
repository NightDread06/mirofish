<template>
  <Transition name="slide-up">
    <div v-if="showBanner" class="cookie-banner">
      <div class="cookie-inner">
        <div class="cookie-text">
          <strong>Cookies</strong> — We use only essential session cookies required for authentication.
          No advertising or tracking cookies.
          <router-link to="/agency/privacy">Privacy Policy →</router-link>
        </div>
        <div class="cookie-actions">
          <button class="btn-accept" @click="accept">Accept</button>
          <router-link to="/agency/privacy" class="btn-learn">Learn More</router-link>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const showBanner = ref(false)

onMounted(() => {
  const consent = localStorage.getItem('agency_cookie_consent')
  if (!consent) showBanner.value = true
})

function accept() {
  localStorage.setItem('agency_cookie_consent', 'accepted')
  showBanner.value = false
}
</script>

<style scoped>
.cookie-banner {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #111;
  color: #fff;
  padding: 16px 24px;
  z-index: 2000;
  font-family: 'Courier New', monospace;
  border-top: 2px solid #fff;
}
.cookie-inner {
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  flex-wrap: wrap;
}
.cookie-text {
  font-size: 0.85rem;
  line-height: 1.5;
  flex: 1;
}
.cookie-text a {
  color: #ccc;
  margin-left: 6px;
}
.cookie-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-shrink: 0;
}
.btn-accept {
  background: #fff;
  color: #111;
  border: 2px solid #fff;
  padding: 8px 20px;
  font-family: inherit;
  font-size: 0.88rem;
  font-weight: bold;
  cursor: pointer;
}
.btn-accept:hover { background: #eee; }
.btn-learn {
  color: #ccc;
  font-size: 0.85rem;
  text-decoration: underline;
}

.slide-up-enter-active, .slide-up-leave-active { transition: transform 0.3s ease; }
.slide-up-enter-from, .slide-up-leave-to { transform: translateY(100%); }
</style>
