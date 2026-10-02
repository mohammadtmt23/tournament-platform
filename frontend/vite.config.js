import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In dev, /api/* is forwarded to the FastAPI server (prefix stripped).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
