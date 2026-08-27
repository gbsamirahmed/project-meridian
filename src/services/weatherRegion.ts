import {
  WEATHER_GRID_COLUMNS,
  WEATHER_GRID_MAX_SPAN_DEGREES,
  WEATHER_GRID_MIN_ZOOM,
  WEATHER_GRID_PADDING_RATIO,
  WEATHER_GRID_REFRESH_INSET_RATIO,
  WEATHER_GRID_ROWS,
  WEATHER_GRID_VISIBLE_INSET_RATIO,
} from "../config/gridConfig";

import type maplibregl from "maplibre-gl";
import type {
  WeatherGrid,
  WeatherGridBounds,
  WeatherGridRequest,
} from "../types/weatherGrid";

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.max(minimum, Math.min(maximum, value));
}

function getVisibleBounds(
  map: maplibregl.Map
): WeatherGridBounds | null {
  const center = map.getCenter();
  const container = map.getContainer();
  const width = container.clientWidth;
  const height = container.clientHeight;
  const sampleXs = [0, width * 0.25, width * 0.5, width * 0.75, width];
  const sampleYs = [0, height * 0.25, height * 0.5, height * 0.75, height];
  const longitudes: number[] = [];
  const latitudes: number[] = [];

  // Sampling the projected viewport captures the true ground footprint of
  // pitched and rotated cameras. Normalising longitude around the map centre
  // avoids a false 360-degree span near the antimeridian.
  for (const y of sampleYs) {
    for (const x of sampleXs) {
      try {
        const location = map.unproject([x, y]);
        const longitudeDelta =
          ((location.lng - center.lng + 540) % 360) - 180;

        if (Number.isFinite(longitudeDelta) && Number.isFinite(location.lat)) {
          longitudes.push(center.lng + longitudeDelta);
          latitudes.push(clamp(location.lat, -84, 84));
        }
      } catch {
        // A globe pixel outside the planet has no geographic footprint.
      }
    }
  }

  if (longitudes.length === 0 || latitudes.length === 0) return null;

  const west = Math.min(...longitudes);
  const east = Math.max(...longitudes);

  if (west < -180 || east > 180) {
    return null;
  }

  return {
    west,
    south: Math.min(...latitudes),
    east,
    north: Math.max(...latitudes),
  };
}

function insetBounds(
  bounds: WeatherGridBounds,
  ratio: number
): WeatherGridBounds {
  const longitudeInset = (bounds.east - bounds.west) * ratio;
  const latitudeInset = (bounds.north - bounds.south) * ratio;

  return {
    west: bounds.west + longitudeInset,
    south: bounds.south + latitudeInset,
    east: bounds.east - longitudeInset,
    north: bounds.north - latitudeInset,
  };
}

function boundsContain(
  outer: WeatherGridBounds,
  inner: WeatherGridBounds
): boolean {
  return (
    inner.west >= outer.west &&
    inner.east <= outer.east &&
    inner.south >= outer.south &&
    inner.north <= outer.north
  );
}

export function createWeatherGridRequest(
  map: maplibregl.Map
): WeatherGridRequest | null {
  if (map.getZoom() < WEATHER_GRID_MIN_ZOOM) return null;

  const visible = getVisibleBounds(map);

  if (!visible) return null;

  const center = map.getCenter();
  const visibleLongitudeSpan = Math.max(0.08, visible.east - visible.west);
  const visibleLatitudeSpan = Math.max(0.06, visible.north - visible.south);
  const longitudeSpan = Math.min(
    WEATHER_GRID_MAX_SPAN_DEGREES,
    visibleLongitudeSpan * (1 + WEATHER_GRID_PADDING_RATIO * 2)
  );
  const latitudeSpan = Math.min(
    WEATHER_GRID_MAX_SPAN_DEGREES,
    visibleLatitudeSpan * (1 + WEATHER_GRID_PADDING_RATIO * 2)
  );

  let west = center.lng - longitudeSpan / 2;
  let east = center.lng + longitudeSpan / 2;

  if (west < -180) {
    east += -180 - west;
    west = -180;
  }

  if (east > 180) {
    west -= east - 180;
    east = 180;
  }

  const south = clamp(center.lat - latitudeSpan / 2, -84, 84);
  const north = clamp(center.lat + latitudeSpan / 2, -84, 84);

  return {
    bounds: { west, south, east, north },
    rows: WEATHER_GRID_ROWS,
    columns: WEATHER_GRID_COLUMNS,
  };
}

export function weatherGridContainsViewport(
  map: maplibregl.Map,
  grid: WeatherGrid
): boolean {
  const visible = getVisibleBounds(map);

  if (!visible) return false;

  return boundsContain(
    insetBounds(grid.bounds, WEATHER_GRID_REFRESH_INSET_RATIO),
    visible
  );
}

export function weatherGridCoversViewport(
  map: maplibregl.Map,
  grid: WeatherGrid
): boolean {
  const visible = getVisibleBounds(map);

  if (!visible) return false;

  return boundsContain(
    insetBounds(grid.bounds, WEATHER_GRID_VISIBLE_INSET_RATIO),
    visible
  );
}
