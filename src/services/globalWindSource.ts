import type maplibregl from "maplibre-gl";

import {
  clearNumericTilePins,
  getCachedVectorTile,
  loadVectorTile,
  setNumericTilePins,
} from "./numericTileCache";
import { resolveVectorTileUrl } from "./globalWeatherService";

import type {
  VectorWeatherFieldSource,
  VectorWeatherTimestep,
} from "../types/globalWeather";
import type { MutableWindVector } from "./weatherInterpolation";
import type { WindVectorField } from "./windField";

const MERCATOR_LATITUDE_LIMIT = 85.05112878;
const COVERAGE_DEBOUNCE_MS = 180;

interface TileCoordinate {
  zoom: number;
  x: number;
  y: number;
}

let fieldInstance = 0;

function wrapLongitude(longitude: number): number {
  return ((longitude + 180) % 360 + 360) % 360 - 180;
}

function longitudeToWorldX(longitude: number, worldSize: number): number {
  return ((((longitude + 180) % 360) + 360) % 360) / 360 * worldSize - 0.5;
}

function latitudeToWorldY(latitude: number, worldSize: number): number {
  const limited = Math.max(
    -MERCATOR_LATITUDE_LIMIT,
    Math.min(MERCATOR_LATITUDE_LIMIT, latitude)
  );
  const sine = Math.sin((limited * Math.PI) / 180);
  return (
    (0.5 - Math.log((1 + sine) / (1 - sine)) / (4 * Math.PI)) *
      worldSize -
    0.5
  );
}

function tileKey(tile: TileCoordinate): string {
  return `${tile.zoom}/${tile.x}/${tile.y}`;
}

function parentTile(tile: TileCoordinate): TileCoordinate | null {
  if (tile.zoom <= 0) return null;
  return {
    zoom: tile.zoom - 1,
    x: Math.floor(tile.x / 2),
    y: Math.floor(tile.y / 2),
  };
}

function collectGlobeTiles(maxZoom: number): TileCoordinate[] {
  const targetZoom = Math.min(2, maxZoom);
  const result: TileCoordinate[] = [{ zoom: 0, x: 0, y: 0 }];
  const count = 2 ** targetZoom;
  for (let y = 0; y < count; y++) {
    for (let x = 0; x < count; x++) {
      result.push({ zoom: targetZoom, x, y });
    }
  }
  return result;
}

function collectViewportTiles(
  map: maplibregl.Map,
  zoom: number
): TileCoordinate[] {
  const count = 2 ** zoom;
  const container = map.getContainer();
  const seeds = new Map<string, TileCoordinate>();
  for (let row = 0; row <= 4; row++) {
    for (let column = 0; column <= 4; column++) {
      try {
        const point = map.unproject([
          (container.clientWidth * column) / 4,
          (container.clientHeight * row) / 4,
        ]);
        if (
          !Number.isFinite(point.lng) ||
          !Number.isFinite(point.lat) ||
          Math.abs(point.lat) > MERCATOR_LATITUDE_LIMIT
        ) {
          continue;
        }
        const x = Math.floor((((wrapLongitude(point.lng) + 180) / 360) * count));
        const worldSize = count * 256;
        const y = Math.floor(latitudeToWorldY(point.lat, worldSize) / 256);
        for (let yOffset = -1; yOffset <= 1; yOffset++) {
          const paddedY = y + yOffset;
          if (paddedY < 0 || paddedY >= count) continue;
          for (let xOffset = -1; xOffset <= 1; xOffset++) {
            const paddedX = ((x + xOffset) % count + count) % count;
            const tile = { zoom, x: paddedX, y: paddedY };
            seeds.set(tileKey(tile), tile);
          }
        }
      } catch {
        // Sky pixels in a pitched view do not necessarily intersect the map.
      }
    }
  }
  return [...seeds.values()];
}

function withParents(tiles: TileCoordinate[]): TileCoordinate[] {
  const result = new Map<string, TileCoordinate>();
  for (const tile of tiles) {
    let current: TileCoordinate | null = tile;
    while (current) {
      result.set(tileKey(current), current);
      current = parentTile(current);
    }
  }
  return [...result.values()];
}

export class GlobalWindVectorField implements WindVectorField {
  readonly bounds = {
    west: -180,
    south: -MERCATOR_LATITUDE_LIMIT,
    east: 180,
    north: MERCATOR_LATITUDE_LIMIT,
  };
  readonly signature: string;
  readonly isGlobal = true;
  readonly source: VectorWeatherFieldSource;
  readonly timestep: VectorWeatherTimestep;

  private readonly pinOwner: string;
  private coverageGeneration = 0;
  private coverageTimer: number | null = null;
  private disposed = false;

  constructor(
    source: VectorWeatherFieldSource,
    timestep: VectorWeatherTimestep
  ) {
    this.source = source;
    this.timestep = timestep;
    this.signature = `${source.manifest.id}:${timestep.id}`;
    this.pinOwner = `wind:${this.signature}:${++fieldInstance}`;
  }

  async prepareCoverage(map: maplibregl.Map): Promise<boolean> {
    const generation = ++this.coverageGeneration;
    const maxZoom = this.source.manifest.tiles.maxZoom;
    const isGlobe = map.getProjection()?.type === "globe";
    const targetTiles = isGlobe
      ? collectGlobeTiles(maxZoom)
      : collectViewportTiles(map, maxZoom);
    const tiles = withParents(
      targetTiles.length ? targetTiles : [{ zoom: 0, x: 0, y: 0 }]
    );
    const results = await Promise.allSettled(
      tiles.map((tile) =>
        loadVectorTile(
          this.source,
          this.timestep,
          tile.zoom,
          tile.x,
          tile.y
        )
      )
    );
    if (this.disposed || generation !== this.coverageGeneration) return false;
    if (results.some((result) => result.status === "rejected")) return false;
    setNumericTilePins(
      this.pinOwner,
      tiles.map((tile) =>
        resolveVectorTileUrl(
          this.source,
          this.timestep,
          tile.zoom,
          tile.x,
          tile.y
        )
      )
    );
    return true;
  }

  scheduleCoverage(map: maplibregl.Map): void {
    if (this.coverageTimer !== null) window.clearTimeout(this.coverageTimer);
    this.coverageTimer = window.setTimeout(() => {
      this.coverageTimer = null;
      void this.prepareCoverage(map);
    }, COVERAGE_DEBOUNCE_MS);
  }

  sample(
    latitude: number,
    longitude: number,
    target: MutableWindVector
  ): boolean {
    if (
      this.disposed ||
      !Number.isFinite(latitude) ||
      !Number.isFinite(longitude) ||
      Math.abs(latitude) > MERCATOR_LATITUDE_LIMIT
    ) {
      return false;
    }
    for (
      let zoom = this.source.manifest.tiles.maxZoom;
      zoom >= this.source.manifest.tiles.minZoom;
      zoom--
    ) {
      if (this.sampleAtZoom(latitude, longitude, zoom, target)) return true;
    }
    return false;
  }

  dispose(): void {
    this.disposed = true;
    this.coverageGeneration++;
    if (this.coverageTimer !== null) window.clearTimeout(this.coverageTimer);
    this.coverageTimer = null;
    clearNumericTilePins(this.pinOwner);
  }

  private sampleAtZoom(
    latitude: number,
    longitude: number,
    zoom: number,
    target: MutableWindVector
  ): boolean {
    const { tileSize, componentScale, componentBias, noDataCode } =
      this.source.manifest.tiles;
    const count = 2 ** zoom;
    const worldSize = count * tileSize;
    const worldX = longitudeToWorldX(longitude, worldSize);
    const worldY = latitudeToWorldY(latitude, worldSize);
    const x0 = Math.floor(worldX);
    const y0 = Math.floor(worldY);
    const xWeight = worldX - x0;
    const yWeight = worldY - y0;
    const samples = [
      this.readPixel(zoom, x0, y0),
      this.readPixel(zoom, x0 + 1, y0),
      this.readPixel(zoom, x0, y0 + 1),
      this.readPixel(zoom, x0 + 1, y0 + 1),
    ];
    if (
      samples.some(
        (sample) =>
          !sample ||
          sample.uCode === noDataCode ||
          sample.vCode === noDataCode
      )
    ) {
      return false;
    }
    const [topLeft, topRight, bottomLeft, bottomRight] = samples as Array<{
      uCode: number;
      vCode: number;
    }>;
    const decode = (code: number) => (code - componentBias) * componentScale;
    const interpolate = (key: "uCode" | "vCode") => {
      const top = decode(topLeft[key]) * (1 - xWeight) + decode(topRight[key]) * xWeight;
      const bottom =
        decode(bottomLeft[key]) * (1 - xWeight) +
        decode(bottomRight[key]) * xWeight;
      return top * (1 - yWeight) + bottom * yWeight;
    };
    const eastwardFlow = interpolate("uCode");
    const northwardFlow = interpolate("vCode");
    const flowBearing =
      ((Math.atan2(eastwardFlow, northwardFlow) * 180) / Math.PI + 360) %
      360;
    target.eastwardFlow = eastwardFlow;
    target.northwardFlow = northwardFlow;
    target.speed = Math.hypot(eastwardFlow, northwardFlow);
    target.flowBearing = flowBearing;
    target.fromDirection = (flowBearing + 180) % 360;
    return true;
  }

  private readPixel(
    zoom: number,
    pixelX: number,
    pixelY: number
  ): { uCode: number; vCode: number } | null {
    const { tileSize } = this.source.manifest.tiles;
    const count = 2 ** zoom;
    const worldSize = count * tileSize;
    const wrappedX = ((pixelX % worldSize) + worldSize) % worldSize;
    const limitedY = Math.max(0, Math.min(worldSize - 1, pixelY));
    const x = Math.floor(wrappedX / tileSize);
    const y = Math.floor(limitedY / tileSize);
    const localX = wrappedX % tileSize;
    const localY = limitedY % tileSize;
    const tile = getCachedVectorTile(
      this.source,
      this.timestep,
      zoom,
      x,
      y
    );
    if (!tile) return null;
    const index = localY * tile.size + localX;
    return { uCode: tile.uCodes[index], vCode: tile.vCodes[index] };
  }
}
