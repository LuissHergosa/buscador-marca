import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": "/src",
    },
  },
  server: {
    host: '0.0.0.0', // Allow external connections (Docker)
    port: 5173,
    watch: {
      usePolling: true, // Enable polling for Docker on Windows
    },
    hmr: {
      port: 5173, // Hot Module Replacement port
    },
  },
})
