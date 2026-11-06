import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const backend = process.env.DEVLAB_BACKEND_URL || 'http://127.0.0.1:8000'
const proxy = { '/api/': { target: backend }, '/ws/': { target: backend, ws: true } }

export default defineConfig({
  plugins: [react()],
  base: '/',
  appType: 'spa',
  server: { proxy },
  preview: { proxy },
})
