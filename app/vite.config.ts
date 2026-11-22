import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // maplibre in its own chunk (cached separately), preloaded from index.html by Vite.
  build: { chunkSizeWarningLimit: 1200, rollupOptions: { output: { manualChunks(id: string) { if (id.includes('maplibre-gl')) return 'maplibre' } } } },
})
