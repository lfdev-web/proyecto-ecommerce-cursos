import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    watch: {
      // Docker en Windows: los eventos de cambio de archivos no atraviesan el
      // bind mount, así que sin polling Vite sirve versiones viejas en caché.
      usePolling: true,
      interval: 300,
    },
    proxy: {
      // Reenvía /api al backend Django. Dentro de docker-compose el nombre
      // de servicio "backend" resuelve por DNS interno de la red del compose.
      '/api': {
        target: process.env.VITE_API_PROXY_TARGET || 'http://backend:8000',
        changeOrigin: true,
      },
      // Archivos subidos (avatares): el backend responde /media/... con URL
      // relativa, así que el dev server también debe reenviarlos a Django.
      '/media': {
        target: process.env.VITE_API_PROXY_TARGET || 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
})
