import maplibregl from "maplibre-gl";

import { LAYER_VISUAL_STRENGTHS } from "../config/layerVisuals";
import { WEATHER_GRID_MIN_ZOOM } from "../config/gridConfig";
import { getFirstSymbolLayerId } from "./mapLayerOrder";
import { interpolateWeatherAtLocation } from "./weatherInterpolation";

import type { WeatherGrid } from "../types/weatherGrid";

const SOURCE_ID = "wind-field-source";
const HALO_LAYER_ID = "wind-field-halo";
const LAYER_ID = "wind-field-layer";

interface WindProperties {
  windSpeed: number;
}

type WindFeatureCollection = GeoJSON.FeatureCollection<
  GeoJSON.MultiLineString,
  WindProperties
>;

let activeSignature: string | null = null;
let coverageVisible = true;

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.max(minimum, Math.min(maximum, value));
}

function offsetCoordinate(
  origin: [number, number],
  bearing: number,
  distance: number
): [number, number] {
  const radians = (bearing * Math.PI) / 180;
  const latitudeScale = Math.max(0.2, Math.cos((origin[1] * Math.PI) / 180));

  return [
    origin[0] + (Math.sin(radians) * distance) / latitudeScale,
    origin[1] + Math.cos(radians) * distance,
  ];
}

function isInsideSafeCoverage(
  longitude: number,
  latitude: number,
  grid: WeatherGrid
): boolean {
  const longitudeInset = (grid.bounds.east - grid.bounds.west) * 0.08;
  const latitudeInset = (grid.bounds.north - grid.bounds.south) * 0.08;

  return (
    longitude >= grid.bounds.west + longitudeInset &&
    longitude <= grid.bounds.east - longitudeInset &&
    latitude >= grid.bounds.south + latitudeInset &&
    latitude <= grid.bounds.north - latitudeInset
  );
}

function buildWindGeoJson(
  map: maplibregl.Map,
  grid: WeatherGrid,
  forecastHour: number
): WindFeatureCollection {
  const container = map.getContainer();
  const width = container.clientWidth;
  const height = container.clientHeight;
  const isMobile = width <= 500;
  const spacing = isMobile ? 74 : 68;
  const edgePadding = spacing * 0.55;
  const features: WindFeatureCollection["features"] = [];
  let rowIndex = 0;

  // Positions are screen-spaced and staggered, but values remain bilinearly
  // interpolated from the same coarse model grid. More arrows communicate the
  // field more legibly; they do not represent higher forecast resolution.
  for (let y = edgePadding; y <= height - edgePadding; y += spacing) {
    const rowOffset = rowIndex % 2 === 0 ? 0 : spacing / 2;

    for (
      let x = edgePadding + rowOffset;
      x <= width - edgePadding;
      x += spacing
    ) {
      const columnIndex = Math.round((x - edgePadding - rowOffset) / spacing);
      const horizontalJitter =
        ((((rowIndex + 3) * 17 + (columnIndex + 5) * 29) % 19) - 9) *
        1.32;
      const verticalJitter =
        ((((rowIndex + 7) * 31 + (columnIndex + 2) * 13) % 17) - 8) *
        1.18;
      const placementHash =
        ((rowIndex + 11) * 37 + (columnIndex + 13) * 43) % 17;

      if (placementHash === 0) continue;
      const sampleX = x + horizontalJitter;
      const sampleY = y + verticalJitter;
      let location: maplibregl.LngLat;

      try {
        location = map.unproject([sampleX, sampleY]);
      } catch {
        continue;
      }

      if (!isInsideSafeCoverage(location.lng, location.lat, grid)) continue;

      const weather = interpolateWeatherAtLocation(
        grid,
        forecastHour,
        location.lat,
        location.lng
      );

      if (!weather) continue;

      const projectedDirection = map.project(
        offsetCoordinate(
          [location.lng, location.lat],
          weather.windFlowBearing,
          0.02
        )
      );
      const dx = projectedDirection.x - sampleX;
      const dy = projectedDirection.y - sampleY;
      const magnitude = Math.hypot(dx, dy);

      if (!Number.isFinite(magnitude) || magnitude < 0.1) continue;

      const unitX = dx / magnitude;
      const unitY = dy / magnitude;
      const length = 24 + clamp(weather.windSpeed, 0, 65) * 0.32;
      const halfLength = length / 2;
      const endX = sampleX + unitX * halfLength;
      const endY = sampleY + unitY * halfLength;
      const startX = sampleX - unitX * halfLength;
      const startY = sampleY - unitY * halfLength;
      const headLength = clamp(length * 0.28, 7, 11);
      const perpendicularX = -unitY;
      const perpendicularY = unitX;
      const headBaseX = endX - unitX * headLength;
      const headBaseY = endY - unitY * headLength;
      const headWidth = headLength * 0.52;

      const start = map.unproject([startX, startY]);
      const end = map.unproject([endX, endY]);
      const leftHead = map.unproject([
        headBaseX + perpendicularX * headWidth,
        headBaseY + perpendicularY * headWidth,
      ]);
      const rightHead = map.unproject([
        headBaseX - perpendicularX * headWidth,
        headBaseY - perpendicularY * headWidth,
      ]);

      features.push({
        type: "Feature",
        geometry: {
          type: "MultiLineString",
          coordinates: [
            [[start.lng, start.lat], [end.lng, end.lat]],
            [
              [leftHead.lng, leftHead.lat],
              [end.lng, end.lat],
              [rightHead.lng, rightHead.lat],
            ],
          ],
        },
        properties: { windSpeed: weather.windSpeed },
      });
    }

    rowIndex += 1;
  }

  return { type: "FeatureCollection", features };
}

function getViewSignature(map: maplibregl.Map): string {
  const center = map.getCenter();
  const container = map.getContainer();

  return [
    center.lng.toFixed(3),
    center.lat.toFixed(3),
    map.getZoom().toFixed(2),
    map.getBearing().toFixed(0),
    map.getPitch().toFixed(0),
    container.clientWidth,
    container.clientHeight,
  ].join(":");
}

function setLayerOpacity(map: maplibregl.Map, visible: boolean): void {
  if (map.getLayer(HALO_LAYER_ID)) {
    map.setPaintProperty(
      HALO_LAYER_ID,
      "line-opacity",
      visible ? LAYER_VISUAL_STRENGTHS.windHalo : 0
    );
  }

  if (map.getLayer(LAYER_ID)) {
    map.setPaintProperty(
      LAYER_ID,
      "line-opacity",
      visible ? LAYER_VISUAL_STRENGTHS.wind : 0
    );
  }
}

export function updateWindLayer(
  map: maplibregl.Map,
  grid: WeatherGrid,
  forecastHour: number
): void {
  const signature = `${grid.fetchedAt}:${forecastHour}:${getViewSignature(map)}`;
  const source = map.getSource(SOURCE_ID) as maplibregl.GeoJSONSource | undefined;

  if (signature !== activeSignature || !source) {
    const data = buildWindGeoJson(map, grid, forecastHour);

    if (source) source.setData(data);
    else map.addSource(SOURCE_ID, { type: "geojson", data });

    activeSignature = signature;
  }

  const beforeId = getFirstSymbolLayerId(map);

  if (!map.getLayer(HALO_LAYER_ID)) {
    map.addLayer(
      {
        id: HALO_LAYER_ID,
        type: "line",
        source: SOURCE_ID,
        minzoom: WEATHER_GRID_MIN_ZOOM,
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": "#12201f",
          "line-width": [
            "interpolate",
            ["linear"],
            ["get", "windSpeed"],
            0,
            3.2,
            65,
            5.2,
          ],
          "line-opacity": LAYER_VISUAL_STRENGTHS.windHalo,
          "line-blur": 0.25,
        },
      },
      beforeId
    );
  }

  if (!map.getLayer(LAYER_ID)) {
    map.addLayer(
      {
        id: LAYER_ID,
        type: "line",
        source: SOURCE_ID,
        minzoom: WEATHER_GRID_MIN_ZOOM,
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": [
            "interpolate",
            ["linear"],
            ["get", "windSpeed"],
            0,
            "#75c8bd",
            25,
            "#e4c04e",
            55,
            "#ed654b",
          ],
          "line-width": [
            "interpolate",
            ["linear"],
            ["get", "windSpeed"],
            0,
            1.25,
            65,
            2.45,
          ],
          "line-opacity": LAYER_VISUAL_STRENGTHS.wind,
        },
      },
      beforeId
    );
  }

  setLayerOpacity(map, coverageVisible);
}

export function setWindLayerCoverage(
  map: maplibregl.Map,
  visible: boolean
): void {
  coverageVisible = visible;
  setLayerOpacity(map, visible);
}

export function removeWindLayer(map: maplibregl.Map): void {
  activeSignature = null;
  coverageVisible = true;

  if (map.getLayer(LAYER_ID)) map.removeLayer(LAYER_ID);
  if (map.getLayer(HALO_LAYER_ID)) map.removeLayer(HALO_LAYER_ID);
  if (map.getSource(SOURCE_ID)) map.removeSource(SOURCE_ID);
}
