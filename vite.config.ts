import { cpSync } from 'node:fs'
import { relative, resolve } from 'node:path'
import { defineConfig } from 'vite'
import type { Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import {
  createGfsPublicationMiddleware,
  materializeGfsPublication,
  resolveGfsPublicationRoot,
} from './scripts/weather/gfs_publication.mjs'

function publishExternalWeather(): Plugin {
  let publicDir = ''
  let outDir = ''
  let isProductionBuild = false
  const publicationRoot = resolveGfsPublicationRoot({ requireExists: false })
  return {
    name: 'meridian-external-weather-publication',
    config: () => ({ build: { copyPublicDir: false } }),
    configResolved: (config) => {
      isProductionBuild = config.command === 'build'
      publicDir = config.publicDir
      outDir = resolve(config.root, config.build.outDir)
    },
    configureServer: (server) => {
      server.middlewares.use(createGfsPublicationMiddleware({ publicationRoot }))
    },

    closeBundle: () => {
      if (!isProductionBuild) return
      cpSync(publicDir, outDir, {
        recursive: true,
        filter: (source) => {
          const name = relative(publicDir, source).replaceAll('\\', '/')
          return name !== 'weather/gfs' && !name.startsWith('weather/gfs/')
        },
      })
      materializeGfsPublication(resolve(outDir, 'weather/gfs'), { publicationRoot })
    },
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), publishExternalWeather()],
})
