import maplibregl from "maplibre-gl";

import { LAYER_VISUAL_STRENGTHS } from "../config/layerVisuals";
import { buildContourGeoJson } from "./contourGeometry";
import { resolveScalarTileUrl } from "./globalWeatherService";
import { getFirstSymbolLayerId } from "./mapLayerOrder";
import {
  clearNumericTilePins,
  loadNumericTile,
  sampleCachedScalarField,
  setNumericTilePins,
} from "./numericTileCache";
import { buildTemperatureContourData } from "./temperatureContourModel";

import type {
  ScalarWeatherFieldSource,
  ScalarWeatherTimestep,
} from "../types/globalWeather";
import type { WeatherGridBounds } from "../types/weatherGrid";

const SOURCE_ID = "temperature-contours-source";
const HALO_LAYER_ID = "temperature-contours-halo";
const LINE_LAYER_ID = "temperature-contours-layer";
const LABEL_LAYER_ID = "temperature-contour-labels";
const ACTIVE_PIN_OWNER = "temperature-contours-active";
const PENDING_PIN_OWNER = "temperature-contours-pending";
const GLOBE_COVERAGE_ZOOM = 2;

interface TileAddress {
  x: number;
  y: number;
}

interface CoveragePlan {
  zoom: number;
  bounds: WeatherGridBounds;
  tiles: TileAddress[];
  signature: string;
  columns: number;
  rows: number;
}

let activeSignature: string | null = null;
let pendingSignature: string | null = null;
let layerEnabled = true;
let generation = 0;
const reportedFailures = new Set<string>();

function emptyContours() {
  return buildContourGeoJson({
    matrix: [],
    bounds: { west: -180, south: -85, east: 180, north: 85 },
    levels: [],
    formatLabel: String,
    upsampleFactor: 1,
  });
}

function tileY(latitude: number, count: number): number {
  const limited = Math.max(-85.05112878, Math.min(85.05112878, latitude));
  const sine = Math.sin((limited * Math.PI) / 180);
  return (
    (0.5 - Math.log((1 + sine) / (1 - sine)) / (4 * Math.PI)) * count
  );
}

function wrapTileX(x: number, count: number): number {
  return ((x % count) + count) % count;
}

function rounded(value: number, increment: number): number {
  return Math.round(value / increment) * increment;
}

function regionalBounds(map: maplibregl.Map): WeatherGridBounds {
  const visible = map.getBounds();
  let west = visible.getWest();
  let east = visible.getEast();
  while (east <= west) east += 360;
  if (east - west > 360) {
    const center = map.getCenter().lng;
    west = center - 180;
    east = center + 180;
  }
  const longitudeSpan = east - west;
  const latitudeSpan = visible.getNorth() - visible.getSouth();
  const longitudePadding = Math.max(0.75, longitudeSpan * 0.22);
  const latitudePadding = Math.max(0.5, latitudeSpan * 0.22);
  const increment = map.getZoom() >= 9 ? 0.25 : map.getZoom() >= 6 ? 0.5 : 1;
  return {
    west: rounded(west - longitudePadding, increment),
    east: rounded(east + longitudePadding, increment),
    south: Math.max(
      -85.05112878,
      rounded(visible.getSouth() - latitudePadding, increment)
    ),
    north: Math.min(
      85.05112878,
      rounded(visible.getNorth() + latitudePadding, increment)
    ),
  };
}

function buildCoveragePlan(map: maplibregl.Map): CoveragePlan {
  const globe = map.getProjection()?.type === "globe";
  if (globe) {
    const count = 2 ** GLOBE_COVERAGE_ZOOM;
    const tiles = Array.from({ length: count * count }, (_, index) => ({
      x: index % count,
      y: Math.floor(index / count),
    }));
    return {
      zoom: GLOBE_COVERAGE_ZOOM,
      bounds: { west: -180, south: -85, east: 180, north: 85 },
      tiles,
      signature: "globe-z2",
      columns: 361,
      rows: 171,
    };
  }

  const zoom = 3;
  const count = 2 ** zoom;
  const bounds = regionalBounds(map);
  const firstX = Math.floor(((bounds.west + 180) / 360) * count) - 1;
  const lastX = Math.floor(((bounds.east + 180) / 360) * count) + 1;
  const firstY = Math.max(0, Math.floor(tileY(bounds.north, count)) - 1);
  const lastY = Math.min(count - 1, Math.floor(tileY(bounds.south, count)) + 1);
  const unique = new Map<string, TileAddress>();
  for (let rawX = firstX; rawX <= lastX; rawX++) {
    for (let y = firstY; y <= lastY; y++) {
      const x = wrapTileX(rawX, count);
      unique.set(`${x}/${y}`, { x, y });
    }
  }
  const longitudeSpan = bounds.east - bounds.west;
  const latitudeSpan = bounds.north - bounds.south;
  const spacing = Math.max(
    0.05,
    Math.min(0.25, Math.max(longitudeSpan / 180, latitudeSpan / 120))
  );
  return {
    zoom,
    bounds,
    tiles: [...unique.values()],
    signature: [
      "regional-z3",
      bounds.west,
      bounds.south,
      bounds.east,
      bounds.north,
    ].join(":"),
    columns: Math.max(2, Math.min(181, Math.ceil(longitudeSpan / spacing) + 1)),
    rows: Math.max(2, Math.min(121, Math.ceil(latitudeSpan / spacing) + 1)),
  };
}

function setLayerOpacity(map: maplibregl.Map): void {
  if (map.getLayer(HALO_LAYER_ID)) {
    map.setPaintProperty(
      HALO_LAYER_ID,
      "line-opacity",
      layerEnabled ? LAYER_VISUAL_STRENGTHS.temperatureHalo : 0
    );
  }
  if (map.getLayer(LINE_LAYER_ID)) {
    map.setPaintProperty(
      LINE_LAYER_ID,
      "line-opacity",
      layerEnabled ? LAYER_VISUAL_STRENGTHS.temperatureContour : 0
    );
  }
  if (map.getLayer(LABEL_LAYER_ID)) {
    map.setPaintProperty(
      LABEL_LAYER_ID,
      "text-opacity",
      layerEnabled ? 0.92 : 0
    );
  }
}

function ensureLayers(map: maplibregl.Map): void {
  if (!map.getSource(SOURCE_ID)) {
    map.addSource(SOURCE_ID, { type: "geojson", data: emptyContours() });
  }
  const beforeId = getFirstSymbolLayerId(map);
  if (!map.getLayer(HALO_LAYER_ID)) {
    map.addLayer(
      {
        id: HALO_LAYER_ID,
        type: "line",
        source: SOURCE_ID,
        filter: ["==", ["geometry-type"], "LineString"],
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": "#17211f",
          "line-width": ["case", ["get", "emphasized"], 2.7, 1.75],
          "line-opacity": LAYER_VISUAL_STRENGTHS.temperatureHalo,
          "line-blur": 0.35,
        },
      },
      beforeId
    );
  }
  if (!map.getLayer(LINE_LAYER_ID)) {
    map.addLayer(
      {
        id: LINE_LAYER_ID,
        type: "line",
        source: SOURCE_ID,
        filter: ["==", ["geometry-type"], "LineString"],
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": [
            "case",
            ["get", "emphasized"],
            "#dff8ff",
            "#ffb36b",
          ],
          "line-width": ["case", ["get", "emphasized"], 1.85, 1.1],
          "line-opacity": LAYER_VISUAL_STRENGTHS.temperatureContour,
          "line-dasharray": [3, 2],
        },
      },
      beforeId
    );
  }
  if (!map.getLayer(LABEL_LAYER_ID)) {
    map.addLayer(
      {
        id: LABEL_LAYER_ID,
        type: "symbol",
        source: SOURCE_ID,
        filter: ["==", ["geometry-type"], "LineString"],
        layout: {
          "text-field": ["get", "label"],
          "text-font": ["Noto Sans Regular"],
          "text-size": 10.5,
          "symbol-placement": "line",
          "symbol-spacing": ["interpolate", ["linear"], ["zoom"], 1, 320, 8, 180],
          "text-rotation-alignment": "map",
          "text-pitch-alignment": "viewport",
          "text-keep-upright": true,
          "text-max-angle": 35,
          "text-allow-overlap": false,
          "text-padding": 8,
        },
        paint: {
          "text-color": "#fff3e4",
          "text-halo-color": "#17211f",
          "text-halo-width": 1.6,
          "text-opacity": 0.92,
        },
      },
      beforeId
    );
  }
  setLayerOpacity(map);
}

async function prepareContours(
  map: maplibregl.Map,
  source: ScalarWeatherFieldSource,
  timestep: ScalarWeatherTimestep,
  plan: CoveragePlan,
  requestGeneration: number,
  signature: string
): Promise<void> {
  const urls = plan.tiles.map((tile) =>
    resolveScalarTileUrl(source, timestep, plan.zoom, tile.x, tile.y)
  );
  setNumericTilePins(PENDING_PIN_OWNER, urls);
  try {
    await Promise.all(
      plan.tiles.map((tile) =>
        loadNumericTile(source, timestep, plan.zoom, tile.x, tile.y)
      )
    );
    if (requestGeneration !== generation || pendingSignature !== signature) return;

    const matrix = Array.from({ length: plan.rows }, (_, row) => {
      const latitude =
        plan.bounds.north -
        (row / Math.max(1, plan.rows - 1)) *
          (plan.bounds.north - plan.bounds.south);
      return Array.from({ length: plan.columns }, (_, column) => {
        const longitude =
          plan.bounds.west +
          (column / Math.max(1, plan.columns - 1)) *
            (plan.bounds.east - plan.bounds.west);
        const value = sampleCachedScalarField(
          source,
          timestep,
          plan.zoom,
          longitude,
          latitude
        );
        if (value === undefined) {
          throw new Error("Prepared temperature coverage lost a required tile");
        }
        return value ?? Number.NaN;
      });
    });
    const data = buildTemperatureContourData(matrix, plan.bounds, map.getZoom());
    if (data.features.length === 0 && matrix.flat().every(Number.isNaN)) {
      throw new Error("Temperature coverage contains no data");
    }
    if (requestGeneration !== generation || pendingSignature !== signature) return;
    const geoJsonSource = map.getSource(SOURCE_ID) as maplibregl.GeoJSONSource | undefined;
    if (!geoJsonSource) return;
    geoJsonSource.setData(data);
    activeSignature = signature;
    pendingSignature = null;
    setNumericTilePins(ACTIVE_PIN_OWNER, urls);
    clearNumericTilePins(PENDING_PIN_OWNER);
  } catch (error) {
    if (requestGeneration !== generation || pendingSignature !== signature) return;
    pendingSignature = null;
    clearNumericTilePins(PENDING_PIN_OWNER);
    if (!reportedFailures.has(signature)) {
      reportedFailures.add(signature);
      console.warn("Global temperature contour coverage failed", error);
    }
  }
}

export function updateTemperatureContourLayer(
  map: maplibregl.Map,
  source: ScalarWeatherFieldSource,
  timestep: ScalarWeatherTimestep
): void {
  layerEnabled = true;
  ensureLayers(map);
  const plan = buildCoveragePlan(map);
  const signature = `${source.manifest.id}:${timestep.id}:${plan.signature}`;
  if (signature === activeSignature || signature === pendingSignature) {
    setLayerOpacity(map);
    return;
  }
  pendingSignature = signature;
  const requestGeneration = ++generation;
  void prepareContours(map, source, timestep, plan, requestGeneration, signature);
  setLayerOpacity(map);
}

export function setTemperatureContourEnabled(
  map: maplibregl.Map,
  enabled: boolean
): void {
  layerEnabled = enabled;
  setLayerOpacity(map);
}

export function removeTemperatureContourLayer(map: maplibregl.Map): void {
  generation += 1;
  activeSignature = null;
  pendingSignature = null;
  layerEnabled = true;
  reportedFailures.clear();
  clearNumericTilePins(ACTIVE_PIN_OWNER);
  clearNumericTilePins(PENDING_PIN_OWNER);
  if (map.getLayer(LABEL_LAYER_ID)) map.removeLayer(LABEL_LAYER_ID);
  if (map.getLayer(LINE_LAYER_ID)) map.removeLayer(LINE_LAYER_ID);
  if (map.getLayer(HALO_LAYER_ID)) map.removeLayer(HALO_LAYER_ID);
  if (map.getSource(SOURCE_ID)) map.removeSource(SOURCE_ID);
}
