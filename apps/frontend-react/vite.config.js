import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'node:path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  server: {
    host: true, // necesario para que el contenedor sea accesible desde el host
    port: 5173,
    strictPort: true,
    watch: {
      // Descomentar si en Windows/WSL no se recargan los cambios.
      // usePolling: true,
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/pruebas/configuracion.js',
  },
})
