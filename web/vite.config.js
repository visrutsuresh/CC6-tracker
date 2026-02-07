import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // For GitHub Pages: VITE_BASE_PATH is set in the deploy workflow to match your repo name
  base: process.env.VITE_BASE_PATH || '/',
})
