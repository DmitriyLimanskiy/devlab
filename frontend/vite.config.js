import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const proxy = { '/api/': { target: 'http://127.0.0.1:8000' }, '/ws/': { target: 'ws://127.0.0.1:8000', ws: true } }

export default defineConfig({
  plugins: [react()],
  base: '/',
  appType: 'spa',
  server: { proxy },
  preview: { proxy },
})
