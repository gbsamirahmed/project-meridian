import { resolveScalarTileUrl } from "./globalWeatherService";

import type {
  ScalarWeatherFieldSource,
  ScalarWeatherTimestep,
} from "../types/globalWeather";

interface NumericTile {
  values: Uint16Array;
  size: number;
}

const MAX_CACHED_TILES = 96;
const tileCache = new Map<string, NumericTile>();
const pendingTiles = new Map<string, Promise<NumericTile>>();

function retainTile(url: string, tile: NumericTile): NumericTile {
  tileCache.delete(url);
  tileCache.set(url, tile);
  while (tileCache.size > MAX_CACHED_TILES) {
    const oldestKey = tileCache.keys().next().value as string | undefined;
    if (!oldestKey) break;
    tileCache.delete(oldestKey);
  }
  return tile;
}

async function decodeNumericPng(url: string, tileSize: number): Promise<NumericTile> {
  const response = await fetch(url, { cache: "force-cache" });
  if (!response.ok) throw new Error(`Numeric weather tile returned HTTP ${response.status}`);

  const bitmap = await createImageBitmap(await response.blob());
  const canvas = document.createElement("canvas");
  canvas.width = tileSize;
  canvas.height = tileSize;
  const context = canvas.getContext("2d", { willReadFrequently: true });
  if (!context) {
    bitmap.close();
    throw new Error("Could not decode numeric weather tile");
  }

  context.drawImage(bitmap, 0, 0, tileSize, tileSize);
  bitmap.close();
  const rgba = context.getImageData(0, 0, tileSize, tileSize).data;
  const values = new Uint16Array(tileSize * tileSize);
  for (let index = 0; index < values.length; index++) {
    values[index] = rgba[index * 4] * 256 + rgba[index * 4 + 1];
  }
  return { values, size: tileSize };
}

export function loadNumericTile(
  source: ScalarWeatherFieldSource,
  timestep: ScalarWeatherTimestep,
  zoom: number,
  x: number,
  y: number
): Promise<NumericTile> {
  const url = resolveScalarTileUrl(source, timestep, zoom, x, y);
  const cached = tileCache.get(url);
  if (cached) return Promise.resolve(retainTile(url, cached));

  const pending = pendingTiles.get(url);
  if (pending) return pending;

  const request = decodeNumericPng(url, source.manifest.tiles.tileSize)
    .then((tile) => retainTile(url, tile))
    .finally(() => pendingTiles.delete(url));
  pendingTiles.set(url, request);
  return request;
}

function longitudeToWorldX(longitude: number, worldSize: number): number {
  const wrapped = ((longitude + 180) % 360 + 360) % 360;
  return (wrapped / 360) * worldSize - 0.5;
}

function latitudeToWorldY(latitude: number, worldSize: number): number {
  const limited = Math.max(-85.05112878, Math.min(85.05112878, latitude));
  const sine = Math.sin((limited * Math.PI) / 180);
  return (
    (0.5 - Math.log((1 + sine) / (1 - sine)) / (4 * Math.PI)) * worldSize - 0.5
  );
}

async function readWorldPixel(
  source: ScalarWeatherFieldSource,
  timestep: ScalarWeatherTimestep,
  pixelX: number,
  pixelY: number
): Promise<number | null> {
  const { maxZoom, tileSize, noData, scale, offset } = source.manifest.tiles;
  const tileCount = 2 ** maxZoom;
  const worldSize = tileCount * tileSize;
  const wrappedX = ((pixelX % worldSize) + worldSize) % worldSize;
  const limitedY = Math.max(0, Math.min(worldSize - 1, pixelY));
  const tileX = Math.floor(wrappedX / tileSize);
  const tileY = Math.floor(limitedY / tileSize);
  const localX = wrappedX % tileSize;
  const localY = limitedY % tileSize;
  const tile = await loadNumericTile(source, timestep, maxZoom, tileX, tileY);
  const encoded = tile.values[localY * tile.size + localX];
  return encoded === noData ? null : encoded * scale + offset;
}

export async function sampleScalarField(
  source: ScalarWeatherFieldSource,
  timestep: ScalarWeatherTimestep,
  longitude: number,
  latitude: number
): Promise<number | null> {
  if (latitude < source.manifest.coverage.bounds[1] || latitude > source.manifest.coverage.bounds[3]) {
    return null;
  }

  const { maxZoom, tileSize } = source.manifest.tiles;
  const worldSize = 2 ** maxZoom * tileSize;
  const worldX = longitudeToWorldX(longitude, worldSize);
  const worldY = latitudeToWorldY(latitude, worldSize);
  const x0 = Math.floor(worldX);
  const y0 = Math.floor(worldY);
  const xWeight = worldX - x0;
  const yWeight = worldY - y0;
  const [topLeft, topRight, bottomLeft, bottomRight] = await Promise.all([
    readWorldPixel(source, timestep, x0, y0),
    readWorldPixel(source, timestep, x0 + 1, y0),
    readWorldPixel(source, timestep, x0, y0 + 1),
    readWorldPixel(source, timestep, x0 + 1, y0 + 1),
  ]);

  if ([topLeft, topRight, bottomLeft, bottomRight].some((value) => value === null)) {
    return null;
  }
  const top = topLeft! * (1 - xWeight) + topRight! * xWeight;
  const bottom = bottomLeft! * (1 - xWeight) + bottomRight! * xWeight;
  return top * (1 - yWeight) + bottom * yWeight;
}

export function clearNumericTileCache(): void {
  tileCache.clear();
  pendingTiles.clear();
}
