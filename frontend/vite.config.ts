import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    https: {
      key: fs.readFileSync('./localhost-key.pem'),
      cert: fs.readFileSync('./localhost-cert.pem'),
    },
    proxy: {
      '/api': {
        target: 'https://127.0.0.1:5001',
        changeOrigin: true,
        secure: false, // allow self-signed certs for local dev
      },
    },
  },
})
