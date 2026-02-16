import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Optional: dev proxy so frontend can call /api without CORS pain.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000'
    }
  }
})
