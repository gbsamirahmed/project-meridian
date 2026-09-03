import { loadNumericTile, type ScalarNumericTile } from "./numericTileCache";
import type { ScalarWeatherFieldSource, ScalarFieldTimestep } from "../types/globalWeather";

type Rgba = { r: number; g: number; b: number; a: number };

/**
 * MapLibre clamps raster textures at tile edges. Use an edge-inclusive visual
 * grid so both tiles evaluate the very same geographic boundary, rather than
 * stretching two different edge-centre values across the join. This is display
 * resampling only; numeric tiles and inspector sampling remain unchanged.
 */
export function scalarRasterPixels(
  size: number,
  readPixel: (x: number, y: number) => number | null,
  colour: (value: number) => Rgba
): Uint8ClampedArray {
  const pixels = new Uint8ClampedArray(size * size * 4);
  for (let row = 0; row < size; row++) {
    const y = row * size / (size - 1) - 0.5;
    const y0 = Math.floor(y);
    const fy = y - y0;
    for (let column = 0; column < size; column++) {
      const x = column * size / (size - 1) - 0.5;
      const x0 = Math.floor(x);
      const fx = x - x0;
      const a = readPixel(x0, y0);
      const b = readPixel(x0 + 1, y0);
      const c = readPixel(x0, y0 + 1);
      const d = readPixel(x0 + 1, y0 + 1);
      if (a === null || b === null || c === null || d === null) continue;
      const value = (a * (1 - fx) + b * fx) * (1 - fy) +
        (c * (1 - fx) + d * fx) * fy;
      const rgba = colour(value);
      const offset = (row * size + column) * 4;
      pixels[offset] = rgba.r;
      pixels[offset + 1] = rgba.g;
      pixels[offset + 2] = rgba.b;
      pixels[offset + 3] = rgba.a;
    }
  }
  return pixels;
}

export async function loadScalarRasterPixels(
  source: ScalarWeatherFieldSource,
  timestep: ScalarFieldTimestep,
  zoom: number,
  x: number,
  y: number,
  colour: (value: number) => Rgba
): Promise<Uint8ClampedArray> {
  const count = 2 ** zoom;
  const { tileSize: size, noData, scale, offset } = source.manifest.tiles;
  const wrap = (value: number) => ((value % count) + count) % count;
  const clamp = (value: number) => Math.max(0, Math.min(count - 1, value));
  const addresses = new Map<string, { x: number; y: number }>();
  // At most nine neighbours; wrapping/clipping deduplicates low-zoom requests.
  // All reads use the existing bounded, URL-keyed numeric cache.
  for (let dy = -1; dy <= 1; dy++) {
    for (let dx = -1; dx <= 1; dx++) {
      const address = { x: wrap(x + dx), y: clamp(y + dy) };
      addresses.set(`${address.x}/${address.y}`, address);
    }
  }
  const tiles = new Map<string, ScalarNumericTile>();
  const queue = [...addresses];
  let cursor = 0;
  await Promise.all(Array.from({ length: Math.min(3, queue.length) }, async () => {
    while (cursor < queue.length) {
      const [key, address] = queue[cursor++];
      tiles.set(key, await loadNumericTile(source, timestep, zoom, address.x, address.y));
    }
  }));
  return scalarRasterPixels(size, (localX, localY) => {
    const pixelX = x * size + localX;
    const pixelY = Math.max(0, Math.min(count * size - 1, y * size + localY));
    const tileX = wrap(Math.floor(pixelX / size));
    const tileY = Math.floor(pixelY / size);
    const tile = tiles.get(`${tileX}/${tileY}`)!;
    const column = ((pixelX % size) + size) % size;
    const code = tile.values[(pixelY % size) * size + column];
    return code === noData ? null : code * scale + offset;
  }, colour);
}
