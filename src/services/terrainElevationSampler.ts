import {
  TERRARIUM_TILE_TEMPLATE,
  TERRAIN_DEM_NATIVE_MAX_ZOOM,
} from "./terrainLayers";
import type { RouteCoordinate } from "../types/route";

const TILE_SIZE = 256;
const MAX_DECODED_TILES = 96;
const FETCH_CONCURRENCY = 6;
const WEB_MERCATOR_LIMIT = 85.05112878;

interface TilePixels {
  data: Uint8ClampedArray;
  size: number;
  lastUsed: number;
}

interface PixelDemand {
  sampleIndex: number;
  cornerIndex: number;
  localX: number;
  localY: number;
}

const decodedTileCache = new Map<string, TilePixels>();

function wrap(value: number, count: number): number {
  return ((value % count) + count) % count;
}

function tileUrl(zoom: number, x: number, y: number): string {
  return TERRARIUM_TILE_TEMPLATE.replace("{z}", String(zoom))
    .replace("{x}", String(x))
    .replace("{y}", String(y));
}

function trimCache(): void {
  if (decodedTileCache.size <= MAX_DECODED_TILES) return;
  const oldest = [...decodedTileCache.entries()].sort(
    (first, second) => first[1].lastUsed - second[1].lastUsed
  );
  for (const [key] of oldest.slice(0, decodedTileCache.size - MAX_DECODED_TILES)) {
    decodedTileCache.delete(key);
  }
}

async function decodeTile(url: string, signal: AbortSignal): Promise<TilePixels> {
  const cached = decodedTileCache.get(url);
  if (cached) {
    cached.lastUsed = performance.now();
    return cached;
  }
  const response = await fetch(url, { signal });
  if (!response.ok) {
    throw new Error(`Terrain tile returned HTTP ${response.status}`);
  }
  const bitmap = await createImageBitmap(await response.blob());
  try {
    const canvas = document.createElement("canvas");
    canvas.width = bitmap.width;
    canvas.height = bitmap.height;
    const context = canvas.getContext("2d", { willReadFrequently: true });
    if (!context) throw new Error("Terrain tile canvas is unavailable");
    context.drawImage(bitmap, 0, 0);
    const tile = {
      data: context.getImageData(0, 0, bitmap.width, bitmap.height).data,
      size: bitmap.width,
      lastUsed: performance.now(),
    };
    decodedTileCache.set(url, tile);
    trimCache();
    return tile;
  } finally {
    bitmap.close();
  }
}

function worldPixel(coordinate: RouteCoordinate, zoom: number): { x: number; y: number } {
  const worldSize = TILE_SIZE * 2 ** zoom;
  const x = ((coordinate.longitude + 180) / 360) * worldSize;
  const sine = Math.sin((coordinate.latitude * Math.PI) / 180);
  const y =
    (0.5 - Math.log((1 + sine) / (1 - sine)) / (4 * Math.PI)) *
    worldSize;
  return { x, y };
}

function demandKey(
  zoom: number,
  pixelX: number,
  pixelY: number
): { key: string; localX: number; localY: number } {
  const tileCount = 2 ** zoom;
  const worldSize = TILE_SIZE * tileCount;
  const wrappedX = wrap(pixelX, worldSize);
  const limitedY = Math.max(0, Math.min(worldSize - 1, pixelY));
  const tileX = Math.floor(wrappedX / TILE_SIZE);
  const tileY = Math.floor(limitedY / TILE_SIZE);
  return {
    key: tileUrl(zoom, tileX, tileY),
    localX: wrappedX % TILE_SIZE,
    localY: limitedY % TILE_SIZE,
  };
}

function terrariumElevation(data: Uint8ClampedArray, offset: number): number {
  return data[offset] * 256 + data[offset + 1] + data[offset + 2] / 256 - 32768;
}

async function runWithConcurrency(
  tasks: Array<() => Promise<void>>,
  concurrency: number
): Promise<void> {
  let next = 0;
  async function worker(): Promise<void> {
    for (;;) {
      const index = next++;
      if (index >= tasks.length) return;
      await tasks[index]();
    }
  }
  await Promise.all(
    Array.from({ length: Math.min(concurrency, tasks.length) }, () => worker())
  );
}

export async function sampleTerrainElevations(
  coordinates: RouteCoordinate[],
  signal: AbortSignal,
  onProgress?: (completedTiles: number, totalTiles: number) => void
): Promise<Array<number | null>> {
  const zoom = TERRAIN_DEM_NATIVE_MAX_ZOOM;
  const tileDemands = new Map<string, PixelDemand[]>();
  const corners = coordinates.map(() => new Array<number | null>(4).fill(null));
  const weights = coordinates.map((coordinate, sampleIndex) => {
    if (Math.abs(coordinate.latitude) > WEB_MERCATOR_LIMIT) return null;
    const pixel = worldPixel(coordinate, zoom);
    const x0 = Math.floor(pixel.x);
    const y0 = Math.floor(pixel.y);
    [
      [x0, y0],
      [x0 + 1, y0],
      [x0, y0 + 1],
      [x0 + 1, y0 + 1],
    ].forEach(([pixelX, pixelY], cornerIndex) => {
      const demand = demandKey(zoom, pixelX, pixelY);
      const list = tileDemands.get(demand.key) ?? [];
      list.push({
        sampleIndex,
        cornerIndex,
        localX: demand.localX,
        localY: demand.localY,
      });
      tileDemands.set(demand.key, list);
    });
    return { x: pixel.x - x0, y: pixel.y - y0 };
  });
  let completedTiles = 0;
  const tasks = [...tileDemands.entries()].map(([url, demands]) => async () => {
    try {
      const tile = await decodeTile(url, signal);
      for (const demand of demands) {
        const offset = (demand.localY * tile.size + demand.localX) * 4;
        corners[demand.sampleIndex][demand.cornerIndex] = terrariumElevation(
          tile.data,
          offset
        );
      }
    } catch (error) {
      if (signal.aborted) throw error;
    } finally {
      completedTiles += 1;
      onProgress?.(completedTiles, tileDemands.size);
    }
  });
  await runWithConcurrency(tasks, FETCH_CONCURRENCY);
  return corners.map((values, index) => {
    const weight = weights[index];
    if (weight === null || values.some((value) => value === null)) return null;
    const [topLeft, topRight, bottomLeft, bottomRight] = values as number[];
    const top = topLeft * (1 - weight.x) + topRight * weight.x;
    const bottom = bottomLeft * (1 - weight.x) + bottomRight * weight.x;
    return top * (1 - weight.y) + bottom * weight.y;
  });
}
