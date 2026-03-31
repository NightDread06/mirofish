import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
// VITE_BASE_PATH is set to '/mirofish/' in GitHub Pages CI; empty for other hosts
export default defineConfig({
  plugins: [vue()],
  base: process.env.VITE_BASE_PATH || '/',
  server: {
    port: 3000,
    open: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5001',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
