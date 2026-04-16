<template>
  <Transition name="slide-up">
    <div
      v-if="showBanner"
      class="cookie-banner cagency"
      role="region"
      aria-label="Cookie notice"
    >
      <div class="cookie-inner">
        <div class="cookie-text">
          <span class="ca-kicker">Cookies</span>
          <p>
            We use only essential session cookies required for authentication.
            No advertising or tracking cookies.
            <router-link to="/agency/privacy">Privacy policy →</router-link>
          </p>
        </div>
        <div class="cookie-actions">
          <router-link to="/agency/privacy" class="ca-btn secondary on-dark">
            Learn more
          </router-link>
          <button class="ca-btn on-dark" @click="accept">Accept</button>
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
  bottom: 0; left: 0; right: 0;
  background: color-mix(in oklab, var(--void), transparent 8%);
  backdrop-filter: saturate(180%) blur(14px);
  -webkit-backdrop-filter: saturate(180%) blur(14px);
  color: var(--moon);
  padding: var(--s-4) var(--s-5);
  z-index: 2000;
  border-top: 1px solid color-mix(in oklab, var(--moon), transparent 88%);
  box-shadow: 0 -12px 32px -16px oklch(0.10 0.02 270 / 0.35);
}
.cookie-inner {
  max-width: var(--page);
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--s-5);
  flex-wrap: wrap;
}
.cookie-text { flex: 1; min-width: 260px; }
.cookie-text .ca-kicker { color: var(--moon-soft); }
.cookie-text p {
  font-size: var(--small);
  line-height: 1.55;
  margin: 6px 0 0;
  color: color-mix(in oklab, var(--moon), transparent 18%);
  max-width: 640px;
}
.cookie-text a {
  color: var(--moon);
  text-decoration-color: color-mix(in oklab, var(--moon), transparent 55%);
  margin-left: 6px;
}
.cookie-actions {
  display: flex;
  gap: var(--s-3);
  align-items: center;
  flex-shrink: 0;
}

.slide-up-enter-active, .slide-up-leave-active {
  transition: transform var(--dur-4) var(--ease-out),
              opacity var(--dur-3) var(--ease-out);
}
.slide-up-enter-from, .slide-up-leave-to {
  transform: translateY(100%);
  opacity: 0;
}
</style>
