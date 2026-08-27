import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";

import { WEATHER_GRID_REQUEST_DELAY_MS } from "../config/gridConfig";
import {
  placeForecastOverlaysInOrder,
} from "../services/mapLayerOrder";
import {
  removePrecipitationSymbols,
  setPrecipitationSymbolCoverage,
  updatePrecipitationSymbols,
} from "../services/precipitationSymbols";
import {
  removePressureLayer,
  setPressureLayerCoverage,
  updatePressureLayer,
} from "../services/pressureLayer";
import {
  applyTerrainLayerState,
  configurePlanetAndTerrain,
  TERRAIN_EXAGGERATION,
  TERRAIN_MIN_ZOOM,
  updateTerrainActivation,
} from "../services/terrainLayers";
import {
  removeTemperatureContourLayer,
  setTemperatureContourCoverage,
  updateTemperatureContourLayer,
} from "../services/temperatureContourLayer";
import {
  createWeatherGridRequest,
  weatherGridContainsViewport,
  weatherGridCoversViewport,
} from "../services/weatherRegion";
import {
  formatWindDirection,
  interpolateWeatherAtLocation,
} from "../services/weatherInterpolation";
import {
  isWeatherSurfaceLayer,
  removeWeatherSurface,
  setWeatherSurfaceCoverage,
  updateWeatherSurface,
} from "../services/weatherSurface";
import {
  removeWindLayer,
  setWindLayerCoverage,
  updateWindLayer,
} from "../services/windLayer";

import type { PrimaryView, WeatherOverlayState } from "../types/layer";
import type { SelectedLocation } from "../types/location";
import type {
  WeatherGrid,
  WeatherGridRequest,
  WeatherGridStatus,
} from "../types/weatherGrid";

import "maplibre-gl/dist/maplibre-gl.css";

interface MapViewProps {
  selectedLocation: SelectedLocation | null;
  primaryView: PrimaryView;
  weatherOverlays: WeatherOverlayState;
  weatherGrid: WeatherGrid | null;
  weatherGridStatus: WeatherGridStatus;
  forecastHour: number;
  onLocationSelect: (location: SelectedLocation) => void;
  onWeatherGridRequest: (request: WeatherGridRequest) => void;
}

interface InspectionPoint {
  x: number;
  y: number;
  containerWidth: number;
  containerHeight: number;
  latitude: number;
  longitude: number;
  elevation: number | null;
  persistent: boolean;
}

const PRIMARY_VIEW_NAMES: Record<PrimaryView, string> = {
  terrain: "Terrain",
  elevation: "Elevation relief",
  precipitation: "Precipitation",
  clouds: "Cloud cover",
};

function removeForecastVisualizations(map: maplibregl.Map): void {
  removeWeatherSurface(map);
  removeTemperatureContourLayer(map);
  removePressureLayer(map);
  removeWindLayer(map);
  removePrecipitationSymbols(map);
}

function renderVisualizations(
  map: maplibregl.Map,
  primaryView: PrimaryView,
  overlays: WeatherOverlayState,
  grid: WeatherGrid | null,
  forecastHour: number
): void {
  applyTerrainLayerState(map, primaryView);

  if (!grid) {
    removeForecastVisualizations(map);
    return;
  }

  if (isWeatherSurfaceLayer(primaryView)) {
    updateWeatherSurface(map, primaryView, grid, forecastHour);
  } else {
    removeWeatherSurface(map);
  }

  if (overlays.temperatureContours) {
    updateTemperatureContourLayer(map, grid, forecastHour);
  } else {
    removeTemperatureContourLayer(map);
  }

  if (overlays.pressureIsobars) {
    updatePressureLayer(map, grid, forecastHour);
  } else {
    removePressureLayer(map);
  }

  if (overlays.windFlow) {
    updateWindLayer(map, grid, forecastHour);
  } else {
    removeWindLayer(map);
  }

  if (primaryView === "precipitation") {
    updatePrecipitationSymbols(map, grid, forecastHour);
  } else {
    removePrecipitationSymbols(map);
  }

  placeForecastOverlaysInOrder(map);
}

function setForecastCoverage(
  map: maplibregl.Map,
  grid: WeatherGrid | null
): void {
  const visible = grid !== null && weatherGridCoversViewport(map, grid);

  setWeatherSurfaceCoverage(map, visible);
  setTemperatureContourCoverage(map, visible);
  setPressureLayerCoverage(map, visible);
  setWindLayerCoverage(map, visible);
  setPrecipitationSymbolCoverage(map, visible);
}

function createInspectionPoint(
  map: maplibregl.Map,
  location: maplibregl.LngLatLike,
  x: number,
  y: number,
  persistent: boolean
): InspectionPoint {
  const lngLat = maplibregl.LngLat.convert(location);
  const container = map.getContainer();
  const renderedElevation = map.queryTerrainElevation(lngLat);

  return {
    x,
    y,
    containerWidth: container.clientWidth,
    containerHeight: container.clientHeight,
    latitude: lngLat.lat,
    longitude: lngLat.lng,
    elevation:
      renderedElevation === null
        ? null
        : renderedElevation / TERRAIN_EXAGGERATION,
    persistent,
  };
}

function formatElevation(elevation: number | null): string {
  return elevation === null ? "Unavailable" : `≈ ${Math.round(elevation / 10) * 10} m`;
}

function formatForecastTime(grid: WeatherGrid, forecastHour: number): string {
  const time = grid.times[forecastHour];

  return time ? `${time.replace("T", " ")} UTC` : `Forecast +${forecastHour} h`;
}

export default function MapView({
  selectedLocation,
  primaryView,
  weatherOverlays,
  weatherGrid,
  weatherGridStatus,
  forecastHour,
  onLocationSelect,
  onWeatherGridRequest,
}: MapViewProps) {
  const [hoverInspection, setHoverInspection] =
    useState<InspectionPoint | null>(null);
  const [selectedInspection, setSelectedInspection] =
    useState<InspectionPoint | null>(null);

  const mapContainer = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null);
  const requestTimeoutRef = useRef<number | null>(null);
  const weatherRequestInFlightRef = useRef(false);

  const weatherGridRef = useRef<WeatherGrid | null>(weatherGrid);
  const weatherGridStatusRef = useRef(weatherGridStatus);
  const primaryViewRef = useRef(primaryView);
  const weatherOverlaysRef = useRef(weatherOverlays);
  const forecastHourRef = useRef(forecastHour);
  const locationSelectRef = useRef(onLocationSelect);
  const weatherGridRequestRef = useRef(onWeatherGridRequest);

  useEffect(() => {
    weatherGridRef.current = weatherGrid;
  }, [weatherGrid]);

  useEffect(() => {
    weatherGridStatusRef.current = weatherGridStatus;

    if (weatherGridStatus !== "loading") {
      weatherRequestInFlightRef.current = false;
    }
  }, [weatherGridStatus]);

  useEffect(() => {
    primaryViewRef.current = primaryView;
  }, [primaryView]);

  useEffect(() => {
    weatherOverlaysRef.current = weatherOverlays;
  }, [weatherOverlays]);

  useEffect(() => {
    forecastHourRef.current = forecastHour;
  }, [forecastHour]);

  useEffect(() => {
    locationSelectRef.current = onLocationSelect;
  }, [onLocationSelect]);

  useEffect(() => {
    weatherGridRequestRef.current = onWeatherGridRequest;
  }, [onWeatherGridRequest]);

  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: "https://tiles.openfreemap.org/styles/liberty",
      center: [-4.0762, 53.0685],
      zoom: 11.4,
      minZoom: 1.4,
      pitch: 0,
      bearing: 0,
      maxPitch: 72,
      renderWorldCopies: false,
    });
    let pendingPointerEvent: maplibregl.MapMouseEvent | null = null;
    let pointerFrame: number | null = null;

    mapRef.current = map;

    const requestWeatherForViewport = () => {
      if (weatherGridStatusRef.current === "loading") return;
      if (weatherRequestInFlightRef.current) return;

      const currentGrid = weatherGridRef.current;

      if (currentGrid && weatherGridContainsViewport(map, currentGrid)) return;

      const request = createWeatherGridRequest(map);

      if (request) {
        weatherRequestInFlightRef.current = true;
        weatherGridRequestRef.current(request);
      }
    };

    const queueWeatherRequest = () => {
      const currentGrid = weatherGridRef.current;

      if (currentGrid && weatherGridContainsViewport(map, currentGrid)) return;
      if (requestTimeoutRef.current !== null) return;

      requestTimeoutRef.current = window.setTimeout(() => {
        requestTimeoutRef.current = null;
        requestWeatherForViewport();
      }, WEATHER_GRID_REQUEST_DELAY_MS);
    };

    const handleMapMovement = () => {
      setForecastCoverage(map, weatherGridRef.current);
      queueWeatherRequest();
    };

    const handleMapMoveEnd = () => {
      renderVisualizations(
        map,
        primaryViewRef.current,
        weatherOverlaysRef.current,
        weatherGridRef.current,
        forecastHourRef.current
      );
      setForecastCoverage(map, weatherGridRef.current);
      queueWeatherRequest();
    };

    const handlePointerFrame = () => {
      pointerFrame = null;
      const event = pendingPointerEvent;

      if (!event) return;

      setHoverInspection(
        createInspectionPoint(
          map,
          event.lngLat,
          event.point.x,
          event.point.y,
          false
        )
      );
    };

    const refreshSelectedElevation = () => {
      const markerLocation = markerRef.current?.getLngLat();

      if (!markerLocation) return;

      const renderedElevation = map.queryTerrainElevation(markerLocation);

      if (renderedElevation === null) return;

      setSelectedInspection((current) =>
        current
          ? {
              ...current,
              elevation: renderedElevation / TERRAIN_EXAGGERATION,
            }
          : current
      );
    };

    const handleMouseMove = (event: maplibregl.MapMouseEvent) => {
      pendingPointerEvent = event;

      if (pointerFrame === null) {
        pointerFrame = window.requestAnimationFrame(handlePointerFrame);
      }
    };

    map.addControl(
      new maplibregl.NavigationControl({ visualizePitch: true }),
      "top-right"
    );

    map.on("style.load", () => {
      configurePlanetAndTerrain(map);
      renderVisualizations(
        map,
        primaryViewRef.current,
        weatherOverlaysRef.current,
        weatherGridRef.current,
        forecastHourRef.current
      );
      setForecastCoverage(map, weatherGridRef.current);
      queueWeatherRequest();
    });

    map.on("move", handleMapMovement);
    map.on("moveend", handleMapMoveEnd);
    map.on("zoom", () => updateTerrainActivation(map));
    map.on("mousemove", handleMouseMove);
    map.on("mouseleave", () => setHoverInspection(null));
    map.on("idle", refreshSelectedElevation);

    map.on("click", (event) => {
      const point = createInspectionPoint(
        map,
        event.lngLat,
        event.point.x,
        event.point.y,
        true
      );

      setHoverInspection(null);
      setSelectedInspection(point);
      locationSelectRef.current({
        latitude: event.lngLat.lat,
        longitude: event.lngLat.lng,
      });
    });

    return () => {
      if (requestTimeoutRef.current !== null) {
        window.clearTimeout(requestTimeoutRef.current);
      }

      if (pointerFrame !== null) window.cancelAnimationFrame(pointerFrame);

      markerRef.current?.remove();
      markerRef.current = null;
      removeForecastVisualizations(map);
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;

    if (!map?.isStyleLoaded()) return;

    renderVisualizations(
      map,
      primaryView,
      weatherOverlays,
      weatherGrid,
      forecastHour
    );
    setForecastCoverage(map, weatherGrid);

    if (!weatherGrid || !weatherGridContainsViewport(map, weatherGrid)) {
      const request = createWeatherGridRequest(map);

      if (request && !weatherRequestInFlightRef.current) {
        weatherRequestInFlightRef.current = true;
        weatherGridRequestRef.current(request);
      }
    }
  }, [primaryView, weatherOverlays, weatherGrid, forecastHour]);

  useEffect(() => {
    const map = mapRef.current;

    if (!selectedLocation || !map) return;

    const lngLat: [number, number] = [
      selectedLocation.longitude,
      selectedLocation.latitude,
    ];
    const currentCenter = map.getCenter();
    const isLongDistanceMove =
      Math.hypot(
        currentCenter.lng - selectedLocation.longitude,
        currentCenter.lat - selectedLocation.latitude
      ) > 6;
    const cameraOptions = {
      center: lngLat,
      zoom: Math.max(map.getZoom(), 10),
    };

    if (isLongDistanceMove || map.getZoom() < TERRAIN_MIN_ZOOM) {
      map.jumpTo(cameraOptions);
    } else {
      map.easeTo({ ...cameraOptions, duration: 650, essential: true });
    }

    if (markerRef.current) {
      markerRef.current.setLngLat(lngLat);
    } else {
      markerRef.current = new maplibregl.Marker({ color: "#ff7048" })
        .setLngLat(lngLat)
        .addTo(map);
    }

    const container = map.getContainer();

    setSelectedInspection(
      createInspectionPoint(
        map,
        lngLat,
        container.clientWidth / 2,
        container.clientHeight / 2,
        true
      )
    );
  }, [selectedLocation]);

  const activeInspection = hoverInspection ?? selectedInspection;
  const inspectedWeather =
    activeInspection && weatherGrid
      ? interpolateWeatherAtLocation(
          weatherGrid,
          forecastHour,
          activeInspection.latitude,
          activeInspection.longitude
        )
      : null;
  const overlayCount = Object.values(weatherOverlays).filter(Boolean).length;
  const forecastStatus = weatherGridStatus === "loading" ? " · sampling" : "";
  const inspectorLeft = activeInspection
    ? activeInspection.x > activeInspection.containerWidth - 258
      ? Math.max(10, activeInspection.x - 244)
      : activeInspection.x + 14
    : 0;
  const inspectorTop = activeInspection
    ? activeInspection.y > activeInspection.containerHeight - 286
      ? Math.max(10, activeInspection.y - 270)
      : activeInspection.y + 14
    : 0;

  return (
    <div className="map-container-wrapper">
      <div className="map-container" ref={mapContainer} />

      <div className="layer-badge">
        <span className="layer-status-dot" />
        <span>
          {PRIMARY_VIEW_NAMES[primaryView]}
          {overlayCount > 0
            ? ` + ${overlayCount} overlay${overlayCount === 1 ? "" : "s"}`
            : ""}
          {forecastStatus}
        </span>
      </div>

      <div className="map-hint">
        Drag to explore <span /> Hover or tap to inspect
      </div>

      {activeInspection && (
        <div
          className="map-hover-card map-inspector-card"
          style={{ left: inspectorLeft, top: inspectorTop }}
        >
          <div className="inspector-heading">
            <p className="hover-title">
              {activeInspection.persistent ? "Selected point" : "Point forecast"}
            </p>
            <span>
              {activeInspection.latitude.toFixed(4)}, {activeInspection.longitude.toFixed(4)}
            </span>
          </div>

          <div className="inspector-metrics">
            <span>Elevation</span>
            <strong>{formatElevation(activeInspection.elevation)}</strong>

            {inspectedWeather ? (
              <>
                <span>Temperature</span>
                <strong>{inspectedWeather.temperature.toFixed(1)} °C</strong>
                <span>Precipitation</span>
                <strong>
                  {inspectedWeather.precipitation < 0.05
                    ? "Dry"
                    : `${inspectedWeather.precipitation.toFixed(1)} mm`}
                </strong>
                <span>Cloud cover</span>
                <strong>≈ {Math.round(inspectedWeather.cloudCover / 5) * 5}%</strong>
                <span>Pressure</span>
                <strong>{Math.round(inspectedWeather.pressure)} hPa</strong>
                <span>Wind</span>
                <strong>{Math.round(inspectedWeather.windSpeed)} km/h</strong>
                <span>Direction</span>
                <strong>{formatWindDirection(inspectedWeather.windDirection)}</strong>
              </>
            ) : (
              <span className="inspector-unavailable">
                Forecast values are outside the current sampled field.
              </span>
            )}
          </div>

          <small>
            {weatherGrid
              ? formatForecastTime(weatherGrid, forecastHour)
              : "Forecast field loading"}
            {inspectedWeather
              ? ` · interpolated from ${weatherGrid?.rows} × ${weatherGrid?.columns} samples`
              : ""}
          </small>
        </div>
      )}
    </div>
  );
}
