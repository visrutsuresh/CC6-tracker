import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // Use relative paths so assets load correctly from any subpath (e.g. GitHub Pages /cc6-tracker/)
  base: './',
})
