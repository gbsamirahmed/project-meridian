import { defineConfig } from 'vite';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
const root = fileURLToPath(new URL('.', import.meta.url));
const product = process.env.MERIDIAN_TILE_ROOT;
if (!product) throw new Error('Explicit external MERIDIAN_TILE_ROOT required');
export default defineConfig({ root, base: '/', worker: { format: 'es' },
  build: { outDir: resolve(product, 'demo'), emptyOutDir: false, target: 'esnext', sourcemap: false } });
