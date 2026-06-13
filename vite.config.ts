import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

const isPackage = (id: string, packageName: string) =>
  id.includes(`/node_modules/${packageName}/`) || id.includes(`\\node_modules\\${packageName}\\`)

const manualChunks = (id: string) => {
  if (id.includes('vite/preload-helper')) {
    return 'preload-helper'
  }

  if (isPackage(id, 'vue') || isPackage(id, 'vue-router') || isPackage(id, 'pinia') || isPackage(id, 'vue-i18n')) {
    return 'vue-vendor'
  }

  if (isPackage(id, 'pdf-lib')) {
    return 'pdf-lib-vendor'
  }

  if (isPackage(id, 'pdfjs-dist')) {
    return 'pdfjs-vendor'
  }

  if (isPackage(id, 'jspdf')) {
    return 'jspdf-vendor'
  }
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  define: {
    'import.meta.env': 'import.meta.env',
  },
  optimizeDeps: {
    include: ['pdf-lib', 'pako'],
  },
  build: {
    target: 'esnext',
    rollupOptions: {
      output: {
        manualChunks,
      },
    },
    chunkSizeWarningLimit: 1000,
  },
  worker: {
    format: 'es',
    plugins: () => [],
  },
  server: {
    port: 3000,
    open: true,
    hmr: {
      overlay: true,
    },
  },
})
