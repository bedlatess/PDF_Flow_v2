import fs from 'node:fs'
import path from 'node:path'
import { defineConfig, mergeConfig, type Plugin } from 'vite'
import baseConfig from './vite.config'

const adminIndexPlugin = (): Plugin => ({
  name: 'pdf-flow-admin-index',
  closeBundle() {
    const outDir = path.resolve(process.cwd(), 'dist-admin')
    const adminHtml = path.join(outDir, 'admin.html')
    const indexHtml = path.join(outDir, 'index.html')

    if (fs.existsSync(adminHtml)) {
      fs.copyFileSync(adminHtml, indexHtml)
    }
  },
})

export default mergeConfig(
  baseConfig,
  defineConfig({
    plugins: [adminIndexPlugin()],
    build: {
      outDir: 'dist-admin',
      rollupOptions: {
        input: 'admin.html',
      },
    },
    server: {
      port: 3001,
      open: false,
    },
    preview: {
      port: 4174,
    },
  }),
)
