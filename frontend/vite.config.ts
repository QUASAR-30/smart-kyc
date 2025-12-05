import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true, // Fail if port 3000 is busy
    // Configuration du Proxy pour rediriger les appels /api vers le backend
    proxy: {
      '/api': {
        target: 'http://localhost:8000', // Localhost for local dev (not Docker)
        changeOrigin: true,
        secure: false,
      }
    }
  }
})