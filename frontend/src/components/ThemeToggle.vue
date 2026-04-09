<template>
  <div class="theme-toggle">
    <button
      @click="toggleTheme"
      :aria-label="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
      class="toggle-btn"
    >
      <svg v-if="isDark" class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <!-- Sun icon -->
        <circle cx="12" cy="12" r="5"/>
        <line x1="12" y1="2" x2="12" y2="4"/>
        <line x1="12" y1="20" x2="12" y2="22"/>
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
        <line x1="2" y1="12" x2="4" y2="12"/>
        <line x1="20" y1="12" x2="22" y2="12"/>
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
      </svg>
      <svg v-else class="icon" viewBox="0 0 24 24" fill="currentColor">
        <!-- Moon icon -->
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
      </svg>
    </button>
  </div>
</template>

<script>
export default {
  name: 'ThemeToggle',
  data() {
    return {
      isDark: false
    };
  },
  methods: {
    toggleTheme() {
      this.isDark = !this.isDark;
      const theme = this.isDark ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', theme);
      localStorage.setItem('theme', theme);
    },
    initTheme() {
      const saved = localStorage.getItem('theme');
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      const theme = saved || (prefersDark ? 'dark' : 'light');
      this.isDark = theme === 'dark';
      document.documentElement.setAttribute('data-theme', theme);
    }
  },
  mounted() {
    this.initTheme();
  }
};
</script>

<style scoped>
.theme-toggle {
  display: flex;
  align-items: center;
}

.toggle-btn {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: var(--spacing-sm);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
  min-height: unset;
  min-width: unset;
}

.toggle-btn:hover {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.icon {
  width: 20px;
  height: 20px;
}

@media (max-width: 640px) {
  .toggle-btn {
    padding: var(--spacing-xs);
  }

  .icon {
    width: 18px;
    height: 18px;
  }
}
</style>
