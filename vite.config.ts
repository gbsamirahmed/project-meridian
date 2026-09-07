import { cpSync } from 'node:fs'
import { relative, resolve } from 'node:path'
import { defineConfig } from 'vite'
import type { Plugin } from 'vite'
import react from '@vitejs/plugin-react'

function copyPublicAssetsWithoutRuntimeLocks(): Plugin {
  let publicDir = ''
  let outDir = ''
  return {
    name: 'meridian-public-assets',
    apply: 'build',
    config: () => ({ build: { copyPublicDir: false } }),
    configResolved: (config) => {
      publicDir = config.publicDir
      outDir = resolve(config.root, config.build.outDir)
    },
    closeBundle: () => cpSync(publicDir, outDir, {
      recursive: true,
      filter: (source) => relative(publicDir, source).replaceAll('\\', '/') !== 'weather/gfs/.updater.lock',
    }),
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), copyPublicAssetsWithoutRuntimeLocks()],
})
