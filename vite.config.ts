import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // Use /Loop-Tool/ for GitHub Pages, / for Render
  base: process.env.GITHUB_ACTIONS ? '/Loop-Tool/' : '/',
})
