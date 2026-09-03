import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import { accumulationIntervalLabel } from "../services/weatherTimeLabel";
import { precipitationAmountLabel } from "../services/precipitationStyle";

import { WEATHER_GRID_REQUEST_DELAY_MS } from "../config/gridConfig";
import {
  NOMINATIM_ATTRIBUTION,
  OPEN_METEO_ATTRIBUTION,
} from "../config/dataAttribution";
import {
  IS_SATELLITE_CONFIGURED,
  SATELLITE_PROVIDER,
} from "../config/satelliteProvider";
import {
  placeForecastOverlaysInOrder,
} from "../services/mapLayerOrder";
import {
  removeGlobalPrecipitationLayer,
  setGlobalPrecipitationEnabled,
  updateGlobalPrecipitationLayer,
} from "../services/globalPrecipitationLayer";
import {
  removeGlobalCloudLayer,
  setGlobalCloudEnabled,
  updateGlobalCloudLayer,
} from "../services/globalCloudLayer";
import {
  getClosestScalarTimestep,
  getClosestVectorTimestep,
  getScalarTimestepAtTime,
  getVectorTimestepAtTime,
} from "../services/globalWeatherService";
import {
  sampleScalarField,
  sampleVectorField,
} from "../services/numericTileCache";
import {
  removePressureLayer,
  setPressureLayerEnabled,
  setPressureLayerCoverage,
  updatePressureLayer,
} from "../services/pressureLayer";
import {
  applySatelliteLayerState,
  captureSatelliteBasemapLayers,
  ensureSatelliteLayer,
  SATELLITE_SOURCE_ID,
} from "../services/satelliteLayer";
import {
  applyTerrainLayerState,
  configurePlanetAndTerrain,
  TERRAIN_EXAGGERATION,
  TERRAIN_MIN_ZOOM,
  updateTerrainActivation,
} from "../services/terrainLayers";
import {
  removeTemperatureContourLayer,
  setTemperatureContourEnabled,
  updateTemperatureContourLayer,
} from "../services/temperatureContourLayer";
import {
  createWeatherGridRequest,
  weatherGridContainsLocation,
  weatherGridContainsViewport,
  weatherGridOverlapsViewport,
} from "../services/weatherRegion";
import {
  formatWindDirection,
  interpolateWeatherAtLocation,
} from "../services/weatherInterpolation";
import {
  removeWindLayer,
  setWindLayerEnabled,
  updateGlobalWindLayer,
} from "../services/windLayer";
import {
  ROUTE_CASING_LAYER_ID,
  ROUTE_CONDITION_LAYER_ID,
  ROUTE_LINE_LAYER_ID,
  removeRouteLayer,
  updateRouteLayer,
} from "../services/routeLayer";
import { getRouteBounds } from "../services/routeGeometry";

import type { Basemap, MapOverlayState } from "../types/layer";
import type {
  GlobalWeatherStatusRegistry,
  ScalarWeatherFieldSource,
  VectorWeatherFieldSource,
} from "../types/globalWeather";
import type { SatelliteLayerStatus } from "../services/satelliteLayer";
import type { SelectedLocation } from "../types/location";
import type {
  WeatherGrid,
  WeatherGridRequest,
  WeatherGridStatus,
} from "../types/weatherGrid";
import type {
  ResampledRouteGeometry,
  RouteCoordinate,
  TerrainRoute,
} from "../types/route";
import type {
  RouteConditionMode,
  RouteConditions,
} from "../types/routeConditions";

import "maplibre-gl/dist/maplibre-gl.css";

interface MapViewProps {
  selectedLocation: SelectedLocation | null;
  basemap: Basemap;
  mapOverlays: MapOverlayState;
  weatherGrid: WeatherGrid | null;
  weatherGridHistory: WeatherGrid[];
  weatherGridStatus: WeatherGridStatus;
  globalPrecipitationSource: ScalarWeatherFieldSource | null;
  globalCloudSource: ScalarWeatherFieldSource | null;
  globalWindSource: VectorWeatherFieldSource | null;
  globalTemperatureSource: ScalarWeatherFieldSource | null;
  globalWeatherStatuses: GlobalWeatherStatusRegistry;
  activeGlobalValidTime: string | null;
  localForecastHour: number;
  routeGeometry: ResampledRouteGeometry | null;
  terrainRoute: TerrainRoute | null;
  focusedRouteSampleIndex: number | null;
  routeConditions: RouteConditions | null;
  routeConditionMode: RouteConditionMode;
  panelCollapsed: boolean;
  onLocationSelect: (location: SelectedLocation) => void;
  onRouteSampleFocus: (index: number | null) => void;
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

const BASEMAP_NAMES: Record<Basemap, string> = {
  terrain: "Terrain",
  satellite: "Satellite",
};

function removeForecastVisualizations(map: maplibregl.Map): void {
  removeGlobalCloudLayer(map);
  removeGlobalPrecipitationLayer(map);
  removeTemperatureContourLayer(map);
  removePressureLayer(map);
  removeWindLayer(map);
}

function renderVisualizations(
  map: maplibregl.Map,
  basemap: Basemap,
  overlays: MapOverlayState,
  grid: WeatherGrid | null,
  globalPrecipitationSource: ScalarWeatherFieldSource | null,
  globalCloudSource: ScalarWeatherFieldSource | null,
  globalWindSource: VectorWeatherFieldSource | null,
  globalTemperatureSource: ScalarWeatherFieldSource | null,
  activeGlobalValidTime: string | null,
  localForecastHour: number
): void {
  if (!map.isStyleLoaded()) return;

  applySatelliteLayerState(map, basemap === "satellite");
  applyTerrainLayerState(map, basemap, overlays.elevation);

  const cloudTimestep = globalCloudSource
    ? getScalarTimestepAtTime(globalCloudSource, activeGlobalValidTime)
    : null;
  if (overlays.clouds && globalCloudSource && cloudTimestep) {
    updateGlobalCloudLayer(map, globalCloudSource, cloudTimestep);
  } else {
    setGlobalCloudEnabled(map, false);
  }

  const precipitationTimestep = globalPrecipitationSource
    ? getScalarTimestepAtTime(globalPrecipitationSource, activeGlobalValidTime)
    : null;
  if (overlays.precipitation && globalPrecipitationSource && precipitationTimestep) {
    updateGlobalPrecipitationLayer(
      map,
      globalPrecipitationSource,
      precipitationTimestep
    );
  } else {
    setGlobalPrecipitationEnabled(map, false);
  }

  const temperatureTimestep = globalTemperatureSource
    ? getScalarTimestepAtTime(globalTemperatureSource, activeGlobalValidTime)
    : null;
  if (overlays.temperatureContours && globalTemperatureSource && temperatureTimestep) {
    updateTemperatureContourLayer(map, globalTemperatureSource, temperatureTimestep);
  } else {
    setTemperatureContourEnabled(map, false);
  }

  if (overlays.pressureIsobars && grid) {
    updatePressureLayer(map, grid, localForecastHour);
  } else {
    setPressureLayerEnabled(map, false);
  }

  const windTimestep = globalWindSource
    ? getVectorTimestepAtTime(globalWindSource, activeGlobalValidTime)
    : null;
  if (overlays.windFlow && globalWindSource && windTimestep) {
    updateGlobalWindLayer(map, globalWindSource, windTimestep, basemap);
  } else {
    setWindLayerEnabled(map, false);
  }

  placeForecastOverlaysInOrder(map);
}

function setForecastCoverage(
  map: maplibregl.Map,
  grid: WeatherGrid | null
): void {
  const visible = grid !== null && weatherGridOverlapsViewport(map, grid);

  setPressureLayerCoverage(map, visible);
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

function nearestRouteSampleIndex(
  map: maplibregl.Map,
  point: maplibregl.PointLike,
  coordinates: RouteCoordinate[],
  maximumPixels = 14
): number | null {
  const target = maplibregl.Point.convert(point);
  let nearest: number | null = null;
  let bestDistance = maximumPixels;
  coordinates.forEach((coordinate, index) => {
    const projected = map.project([coordinate.longitude, coordinate.latitude]);
    const distance = Math.hypot(projected.x - target.x, projected.y - target.y);
    if (distance <= bestDistance) {
      bestDistance = distance;
      nearest = index;
    }
  });
  return nearest;
}

export default function MapView({
  selectedLocation,
  basemap,
  mapOverlays,
  weatherGrid,
  weatherGridHistory,
  weatherGridStatus,
  globalPrecipitationSource,
  globalCloudSource,
  globalWindSource,
  globalTemperatureSource,
  globalWeatherStatuses,
  activeGlobalValidTime,
  localForecastHour,
  routeGeometry,
  terrainRoute,
  focusedRouteSampleIndex,
  routeConditions,
  routeConditionMode,
  panelCollapsed,
  onLocationSelect,
  onRouteSampleFocus,
  onWeatherGridRequest,
}: MapViewProps) {
  const [hoverInspection, setHoverInspection] =
    useState<InspectionPoint | null>(null);
  const [selectedInspection, setSelectedInspection] =
    useState<InspectionPoint | null>(null);
  const [satelliteStatus, setSatelliteStatus] = useState<SatelliteLayerStatus>(
    IS_SATELLITE_CONFIGURED ? "idle" : "unavailable"
  );
  const [globalPrecipitationSample, setGlobalPrecipitationSample] = useState<{
    key: string;
    value: number | null;
  } | null>(null);
  const [globalCloudSample, setGlobalCloudSample] = useState<{
    key: string;
    value: number | null;
  } | null>(null);
  const [globalWindSample, setGlobalWindSample] = useState<{
    key: string;
    value: { u: number; v: number } | null;
  } | null>(null);
  const [globalTemperatureSample, setGlobalTemperatureSample] = useState<{
    key: string;
    value: number | null;
  } | null>(null);

  const mapContainer = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null);
  const requestTimeoutRef = useRef<number | null>(null);
  const queueWeatherRequestRef = useRef<() => void>(() => undefined);
  const syncSatelliteViewRef = useRef<() => void>(() => undefined);

  const weatherGridRef = useRef<WeatherGrid | null>(weatherGrid);
  const globalPrecipitationSourceRef = useRef(globalPrecipitationSource);
  const globalCloudSourceRef = useRef(globalCloudSource);
  const globalWindSourceRef = useRef(globalWindSource);
  const globalTemperatureSourceRef = useRef(globalTemperatureSource);
  const basemapRef = useRef(basemap);
  const mapOverlaysRef = useRef(mapOverlays);
  const activeGlobalValidTimeRef = useRef(activeGlobalValidTime);
  const localForecastHourRef = useRef(localForecastHour);
  const locationSelectRef = useRef(onLocationSelect);
  const weatherGridRequestRef = useRef(onWeatherGridRequest);
  const routeCoordinatesRef = useRef<RouteCoordinate[]>([]);
  const routeFocusRef = useRef(onRouteSampleFocus);
  const focusedRouteSampleRef = useRef(focusedRouteSampleIndex);
  const routeConditionsRef = useRef(routeConditions);
  const routeConditionModeRef = useRef(routeConditionMode);
  const fittedRouteIdRef = useRef<string | null>(null);
  const activeInspection = hoverInspection ?? selectedInspection;
  const localReferenceTime = weatherGrid?.times[localForecastHour] ?? null;
  const activePrecipitationTimestep = globalPrecipitationSource
    ? getScalarTimestepAtTime(globalPrecipitationSource, activeGlobalValidTime) ??
      getClosestScalarTimestep(globalPrecipitationSource, localReferenceTime)
    : null;
  const activeCloudTimestep = globalCloudSource
    ? getScalarTimestepAtTime(globalCloudSource, activeGlobalValidTime) ??
      getClosestScalarTimestep(globalCloudSource, localReferenceTime)
    : null;
  const activeWindTimestep = globalWindSource
    ? getVectorTimestepAtTime(globalWindSource, activeGlobalValidTime) ??
      getClosestVectorTimestep(globalWindSource, localReferenceTime)
    : null;
  const activeTemperatureTimestep = globalTemperatureSource
    ? getScalarTimestepAtTime(globalTemperatureSource, activeGlobalValidTime) ??
      getClosestScalarTimestep(globalTemperatureSource, localReferenceTime)
    : null;

  useEffect(() => {
    weatherGridRef.current = weatherGrid;
  }, [weatherGrid]);

  useEffect(() => {
    globalPrecipitationSourceRef.current = globalPrecipitationSource;
  }, [globalPrecipitationSource]);

  useEffect(() => {
    globalCloudSourceRef.current = globalCloudSource;
  }, [globalCloudSource]);

  useEffect(() => {
    globalWindSourceRef.current = globalWindSource;
  }, [globalWindSource]);

  useEffect(() => {
    globalTemperatureSourceRef.current = globalTemperatureSource;
  }, [globalTemperatureSource]);

  useEffect(() => {
    basemapRef.current = basemap;
  }, [basemap]);

  useEffect(() => {
    mapOverlaysRef.current = mapOverlays;
  }, [mapOverlays]);

  useEffect(() => {
    activeGlobalValidTimeRef.current = activeGlobalValidTime;
  }, [activeGlobalValidTime]);

  useEffect(() => {
    localForecastHourRef.current = localForecastHour;
  }, [localForecastHour]);

  useEffect(() => {
    locationSelectRef.current = onLocationSelect;
  }, [onLocationSelect]);

  useEffect(() => {
    weatherGridRequestRef.current = onWeatherGridRequest;
  }, [onWeatherGridRequest]);

  useEffect(() => {
    routeFocusRef.current = onRouteSampleFocus;
  }, [onRouteSampleFocus]);

  useEffect(() => {
    focusedRouteSampleRef.current = focusedRouteSampleIndex;
  }, [focusedRouteSampleIndex]);

  useEffect(() => {
    routeConditionsRef.current = routeConditions;
  }, [routeConditions]);

  useEffect(() => {
    routeConditionModeRef.current = routeConditionMode;
  }, [routeConditionMode]);

  // Start point samples immediately. Inspection updates suppress stale results,
  // while the shared tile cache deduplicates requests; delaying here can be
  // perpetually reset by otherwise harmless inspection-state refreshes.
  useEffect(() => {
    if (
      !activeInspection ||
      !globalPrecipitationSource ||
      !activePrecipitationTimestep
    ) {
      return;
    }

    let isCurrent = true;
    const key = [
      globalPrecipitationSource.manifest.id,
      activePrecipitationTimestep.id,
      activeInspection.longitude.toFixed(5),
      activeInspection.latitude.toFixed(5),
    ].join(":");
    sampleScalarField(
      globalPrecipitationSource,
      activePrecipitationTimestep,
      activeInspection.longitude,
      activeInspection.latitude
    )
      .then((value) => {
        if (isCurrent) setGlobalPrecipitationSample({ key, value });
      })
      .catch((error: unknown) => {
        if (isCurrent) {
          console.error("Global precipitation inspection failed", error);
          setGlobalPrecipitationSample({ key, value: null });
        }
      });

    return () => {
      isCurrent = false;
    };
  }, [
    activeInspection,
    activePrecipitationTimestep,
    globalPrecipitationSource,
  ]);

  useEffect(() => {
    if (!activeInspection || !globalCloudSource || !activeCloudTimestep) return;

    let isCurrent = true;
    const key = [
      globalCloudSource.manifest.id,
      activeCloudTimestep.id,
      activeInspection.longitude.toFixed(5),
      activeInspection.latitude.toFixed(5),
    ].join(":");
    sampleScalarField(
      globalCloudSource,
      activeCloudTimestep,
      activeInspection.longitude,
      activeInspection.latitude
    )
      .then((value) => {
        if (isCurrent) setGlobalCloudSample({ key, value });
      })
      .catch((error: unknown) => {
        if (isCurrent) {
          console.error("Global cloud inspection failed", error);
          setGlobalCloudSample({ key, value: null });
        }
      });

    return () => {
      isCurrent = false;
    };
  }, [activeCloudTimestep, activeInspection, globalCloudSource]);

  useEffect(() => {
    if (
      !activeInspection ||
      !globalTemperatureSource ||
      !activeTemperatureTimestep
    ) {
      return;
    }
    let isCurrent = true;
    const key = [
      globalTemperatureSource.manifest.id,
      activeTemperatureTimestep.id,
      activeInspection.longitude.toFixed(5),
      activeInspection.latitude.toFixed(5),
    ].join(":");
    sampleScalarField(
      globalTemperatureSource,
      activeTemperatureTimestep,
      activeInspection.longitude,
      activeInspection.latitude
    )
      .then((value) => {
        if (isCurrent) setGlobalTemperatureSample({ key, value });
      })
      .catch((error: unknown) => {
        if (isCurrent) {
          console.error("Global temperature inspection failed", error);
          setGlobalTemperatureSample({ key, value: null });
        }
      });
    return () => {
      isCurrent = false;
    };
  }, [activeInspection, activeTemperatureTimestep, globalTemperatureSource]);

  useEffect(() => {
    if (!activeInspection || !globalWindSource || !activeWindTimestep) return;
    let isCurrent = true;
    const key = [
      globalWindSource.manifest.id,
      activeWindTimestep.id,
      activeInspection.longitude.toFixed(5),
      activeInspection.latitude.toFixed(5),
    ].join(":");
    sampleVectorField(
      globalWindSource,
      activeWindTimestep,
      activeInspection.longitude,
      activeInspection.latitude
    )
      .then((value) => {
        if (isCurrent) setGlobalWindSample({ key, value });
      })
      .catch((error: unknown) => {
        if (isCurrent) {
          console.error("Global wind inspection failed", error);
          setGlobalWindSample({ key, value: null });
        }
      });
    return () => {
      isCurrent = false;
    };
  }, [activeInspection, activeWindTimestep, globalWindSource]);

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
      // Keep already-requested parent tiles available while higher-resolution
      // children arrive. MapLibre then renders progressive DEM fallbacks during
      // zooming instead of cancelling the lower-detail work mid-transition.
      cancelPendingTileRequestsWhileZooming: false,
      attributionControl: {
        compact: true,
        customAttribution: [OPEN_METEO_ATTRIBUTION, NOMINATIM_ATTRIBUTION],
      },
    });
    let pendingPointerEvent: maplibregl.MapMouseEvent | null = null;
    let pointerFrame: number | null = null;

    mapRef.current = map;

    const syncSatelliteView = () => {
      const shouldShowSatellite = basemapRef.current === "satellite";

      applySatelliteLayerState(map, shouldShowSatellite);
      if (!shouldShowSatellite) return;

      if (!IS_SATELLITE_CONFIGURED) {
        setSatelliteStatus("unavailable");
        return;
      }

      setSatelliteStatus("loading");
      void ensureSatelliteLayer(map).then((status) => {
        if (mapRef.current !== map) return;

        const isStillSelected = basemapRef.current === "satellite";
        applySatelliteLayerState(map, isStillSelected && status === "ready");
        setSatelliteStatus(status === "ready" ? "loading" : status);

        if (status === "ready") {
          renderVisualizations(
            map,
            basemapRef.current,
            mapOverlaysRef.current,
            weatherGridRef.current,
            globalPrecipitationSourceRef.current,
            globalCloudSourceRef.current,
            globalWindSourceRef.current,
            globalTemperatureSourceRef.current,
            activeGlobalValidTimeRef.current,
            localForecastHourRef.current
          );

          if (map.getSource(SATELLITE_SOURCE_ID) && map.isSourceLoaded(SATELLITE_SOURCE_ID)) {
            setSatelliteStatus("ready");
          }
        }
      });
    };

    syncSatelliteViewRef.current = syncSatelliteView;

    const requestWeatherForViewport = () => {
      const currentGrid = weatherGridRef.current;

      if (currentGrid && weatherGridContainsViewport(map, currentGrid)) return;

      const request = createWeatherGridRequest(map);

      if (request) weatherGridRequestRef.current(request);
    };

    const queueWeatherRequest = () => {
      const currentGrid = weatherGridRef.current;

      if (requestTimeoutRef.current !== null) {
        window.clearTimeout(requestTimeoutRef.current);
        requestTimeoutRef.current = null;
      }

      if (currentGrid && weatherGridContainsViewport(map, currentGrid)) return;

      requestTimeoutRef.current = window.setTimeout(() => {
        requestTimeoutRef.current = null;
        requestWeatherForViewport();
      }, WEATHER_GRID_REQUEST_DELAY_MS);
    };

    queueWeatherRequestRef.current = queueWeatherRequest;

    const handleMapMovement = () => {
      setForecastCoverage(map, weatherGridRef.current);
      queueWeatherRequest();
    };

    const handleMapMoveEnd = () => {
      renderVisualizations(
        map,
        basemapRef.current,
        mapOverlaysRef.current,
        weatherGridRef.current,
        globalPrecipitationSourceRef.current,
        globalCloudSourceRef.current,
        globalWindSourceRef.current,
        globalTemperatureSourceRef.current,
        activeGlobalValidTimeRef.current,
        localForecastHourRef.current
      );
      setForecastCoverage(map, weatherGridRef.current);
      queueWeatherRequest();
    };

    const handlePointerFrame = () => {
      pointerFrame = null;
      const event = pendingPointerEvent;

      if (!event) return;

      const routeHitLayers = [
        ROUTE_CASING_LAYER_ID,
        ROUTE_LINE_LAYER_ID,
        ROUTE_CONDITION_LAYER_ID,
      ].filter((layerId) => map.getLayer(layerId));
      const routeIndex =
        routeHitLayers.length > 0 &&
        map.queryRenderedFeatures(event.point, { layers: routeHitLayers }).length > 0
          ? nearestRouteSampleIndex(
              map,
              event.point,
              routeCoordinatesRef.current,
              10
            )
          : null;
      if (routeIndex !== null) {
        routeFocusRef.current(routeIndex);
        setHoverInspection(null);
        return;
      }

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
      captureSatelliteBasemapLayers(map);
      configurePlanetAndTerrain(map);
      renderVisualizations(
        map,
        basemapRef.current,
        mapOverlaysRef.current,
        weatherGridRef.current,
        globalPrecipitationSourceRef.current,
        globalCloudSourceRef.current,
        globalWindSourceRef.current,
        globalTemperatureSourceRef.current,
        activeGlobalValidTimeRef.current,
        localForecastHourRef.current
      );
      setForecastCoverage(map, weatherGridRef.current);
      syncSatelliteView();
      updateRouteLayer(
        map,
        routeCoordinatesRef.current,
        focusedRouteSampleRef.current,
        routeConditionsRef.current,
        routeConditionModeRef.current
      );
      queueWeatherRequest();
    });

    map.on("sourcedata", (event) => {
      if (
        event.sourceId === SATELLITE_SOURCE_ID &&
        map.getSource(SATELLITE_SOURCE_ID) &&
        map.isSourceLoaded(SATELLITE_SOURCE_ID)
      ) {
        setSatelliteStatus("ready");
      }
    });

    map.on("error", (event) => {
      const sourceId = (event as typeof event & { sourceId?: string }).sourceId;

      if (sourceId === SATELLITE_SOURCE_ID) {
        setSatelliteStatus("degraded");
        return;
      }

      console.error(event.error);
    });

    map.on("move", handleMapMovement);
    map.on("moveend", handleMapMoveEnd);
    map.on("movestart", () => setHoverInspection(null));
    // Projection and terrain mutate MapLibre's tile pipeline. Apply that mode
    // change after zooming settles rather than racing it on every zoom frame.
    map.on("zoomend", () => updateTerrainActivation(map));
    map.on("mousemove", handleMouseMove);
    map.on("mouseleave", () => setHoverInspection(null));
    map.on("idle", refreshSelectedElevation);

    map.on("click", (event) => {
      const routeIndex = nearestRouteSampleIndex(
        map,
        event.point,
        routeCoordinatesRef.current
      );
      if (routeIndex !== null) {
        setHoverInspection(null);
        setSelectedInspection(null);
        routeFocusRef.current(routeIndex);
        return;
      }
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
      removeRouteLayer(map);
      map.remove();
      mapRef.current = null;
      queueWeatherRequestRef.current = () => undefined;
      syncSatelliteViewRef.current = () => undefined;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    const coordinates =
      terrainRoute && routeGeometry && terrainRoute.id === routeGeometry.id
        ? terrainRoute.samples
        : routeGeometry?.coordinates ?? [];
    routeCoordinatesRef.current = coordinates;
    if (!map?.isStyleLoaded()) return;
    updateRouteLayer(
      map,
      coordinates,
      focusedRouteSampleIndex,
      routeConditions,
      routeConditionMode
    );
    placeForecastOverlaysInOrder(map);
    if (!routeGeometry) {
      fittedRouteIdRef.current = null;
      return;
    }
    if (fittedRouteIdRef.current === routeGeometry.id) return;
    fittedRouteIdRef.current = routeGeometry.id;
    const bounds = getRouteBounds(routeGeometry.coordinates);
    const center = map.getCenter();
    const routeCenter = (bounds.west + bounds.east) / 2;
    const longitudeDelta = Math.abs(
      ((routeCenter - center.lng + 540) % 360) - 180
    );
    map.fitBounds(
      [
        [bounds.west, bounds.south],
        [bounds.east, bounds.north],
      ],
      {
        padding: {
          top: 70,
          right: 70,
          bottom: 70,
          left: panelCollapsed ? 70 : 410,
        },
        maxZoom: 14,
        bearing: map.getBearing(),
        pitch: map.getPitch(),
        duration: longitudeDelta > 70 ? 0 : 750,
        essential: true,
      }
    );
  }, [
    focusedRouteSampleIndex,
    panelCollapsed,
    routeConditionMode,
    routeConditions,
    routeGeometry,
    terrainRoute,
  ]);

  useEffect(() => {
    const map = mapRef.current;

    if (!map?.isStyleLoaded()) return;

    renderVisualizations(
      map,
      basemap,
      mapOverlays,
      weatherGrid,
      globalPrecipitationSource,
      globalCloudSource,
      globalWindSource,
      globalTemperatureSource,
      activeGlobalValidTime,
      localForecastHour
    );
    setForecastCoverage(map, weatherGrid);
  }, [
    basemap,
    mapOverlays,
    weatherGrid,
    globalPrecipitationSource,
    globalCloudSource,
    globalWindSource,
    globalTemperatureSource,
    activeGlobalValidTime,
    localForecastHour,
  ]);

  useEffect(() => {
    syncSatelliteViewRef.current();
  }, [basemap]);

  useEffect(() => {
    queueWeatherRequestRef.current();
  }, [weatherGrid]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    map.resize();
    const resizeTimer = window.setTimeout(() => map.resize(), 240);
    return () => window.clearTimeout(resizeTimer);
  }, [panelCollapsed]);

  useEffect(() => {
    const map = mapRef.current;

    if (!selectedLocation || !map) return;

    setHoverInspection(null);

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

  const inspectionGrid = activeInspection
    ? [weatherGrid, ...weatherGridHistory].find(
        (grid): grid is WeatherGrid =>
          grid !== null &&
          weatherGridContainsLocation(
            grid,
            activeInspection.latitude,
            activeInspection.longitude
          )
      ) ?? null
    : null;
  const inspectedWeather =
    activeInspection && inspectionGrid
      ? interpolateWeatherAtLocation(
          inspectionGrid,
          localForecastHour,
          activeInspection.latitude,
          activeInspection.longitude
        )
      : null;
  const expectedGlobalSampleKey =
    activeInspection && activePrecipitationTimestep && globalPrecipitationSource
      ? [
          globalPrecipitationSource.manifest.id,
          activePrecipitationTimestep.id,
          activeInspection.longitude.toFixed(5),
          activeInspection.latitude.toFixed(5),
        ].join(":")
      : null;
  const globalPrecipitationValue =
    globalPrecipitationSample?.key === expectedGlobalSampleKey
      ? globalPrecipitationSample.value
      : undefined;
  const expectedGlobalCloudSampleKey =
    activeInspection && activeCloudTimestep && globalCloudSource
      ? [
          globalCloudSource.manifest.id,
          activeCloudTimestep.id,
          activeInspection.longitude.toFixed(5),
          activeInspection.latitude.toFixed(5),
        ].join(":")
      : null;
  const globalCloudValue =
    globalCloudSample?.key === expectedGlobalCloudSampleKey
      ? globalCloudSample.value
      : undefined;
  const expectedGlobalTemperatureSampleKey =
    activeInspection && activeTemperatureTimestep && globalTemperatureSource
      ? [
          globalTemperatureSource.manifest.id,
          activeTemperatureTimestep.id,
          activeInspection.longitude.toFixed(5),
          activeInspection.latitude.toFixed(5),
        ].join(":")
      : null;
  const globalTemperatureValue =
    globalTemperatureSample?.key === expectedGlobalTemperatureSampleKey
      ? globalTemperatureSample.value
      : undefined;
  const expectedGlobalWindSampleKey =
    activeInspection && activeWindTimestep && globalWindSource
      ? [
          globalWindSource.manifest.id,
          activeWindTimestep.id,
          activeInspection.longitude.toFixed(5),
          activeInspection.latitude.toFixed(5),
        ].join(":")
      : null;
  const globalWindValue =
    globalWindSample?.key === expectedGlobalWindSampleKey
      ? globalWindSample.value
      : undefined;
  const globalWindSpeed = globalWindValue
    ? Math.hypot(globalWindValue.u, globalWindValue.v)
    : null;
  const globalWindDirection = globalWindValue
    ? ((180 +
        (Math.atan2(globalWindValue.u, globalWindValue.v) * 180) / Math.PI) %
        360 +
        360) %
      360
    : null;
  const overlayCount = Object.values(mapOverlays).filter(Boolean).length;
  const forecastStatus =
    weatherGridStatus === "loading"
      ? " · sampling"
      : weatherGridStatus === "refreshing"
        ? " · refreshing"
        : weatherGridStatus === "rate-limited"
          ? " · refresh delayed"
          : weatherGridStatus === "error"
            ? " · forecast issue"
          : "";
  const satelliteStatusText =
    basemap !== "satellite"
      ? ""
      : satelliteStatus === "loading"
        ? " · imagery loading"
        : satelliteStatus === "degraded"
          ? " · imagery issue"
        : satelliteStatus === "error"
          ? " · imagery unavailable"
          : "";
  const activeGlobalStatuses = [
    mapOverlays.precipitation ? globalWeatherStatuses.precipitation : null,
    mapOverlays.clouds ? globalWeatherStatuses.cloud_cover : null,
    mapOverlays.windFlow ? globalWeatherStatuses.wind_10m : null,
    mapOverlays.temperatureContours
      ? globalWeatherStatuses.temperature_2m
      : null,
  ].filter(Boolean);
  const globalWeatherStatusText =
    activeGlobalStatuses.length === 0
      ? ""
      : activeGlobalStatuses.some((status) => status === "loading")
        ? " · GFS loading"
        : activeGlobalStatuses.every((status) => status === "ready")
          ? " · GFS 0.25°"
          : " · GFS field unavailable";
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
          {BASEMAP_NAMES[basemap]}
          {overlayCount > 0
            ? ` + ${overlayCount} overlay${overlayCount === 1 ? "" : "s"}`
            : ""}
          {forecastStatus}
          {satelliteStatusText}
          {globalWeatherStatusText}
        </span>
      </div>

      {basemap === "satellite" &&
        IS_SATELLITE_CONFIGURED &&
        satelliteStatus !== "error" && (
        <a
          className={`maptiler-logo${panelCollapsed ? " maptiler-logo-panel-collapsed" : ""}`}
          href={SATELLITE_PROVIDER.providerUrl}
          target="_blank"
          rel="noopener noreferrer"
          aria-label="Satellite imagery by MapTiler"
        >
          <img src={SATELLITE_PROVIDER.logoUrl} alt="MapTiler" />
        </a>
      )}

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

            <span>Temperature (GFS)</span>
            <strong>
              {!globalTemperatureSource
                ? "Unavailable"
                : globalTemperatureValue === undefined
                  ? "Loading…"
                  : globalTemperatureValue === null
                    ? "Unavailable"
                    : `${globalTemperatureValue.toFixed(1)} °C`}
            </strong>

            {(globalPrecipitationSource || globalWeatherStatuses.precipitation !== "ready") && (
              <>
                <span>Precipitation (GFS)</span>
                <strong>{!globalPrecipitationSource
                    ? "Unavailable"
                    : globalPrecipitationValue === undefined
                    ? "Loading…"
                    : globalPrecipitationValue === null
                      ? "Unavailable"
                      : precipitationAmountLabel(globalPrecipitationValue)}</strong>
              </>
            )}

            <span>Cloud cover (GFS)</span>
            <strong>
              {!globalCloudSource
                ? "Unavailable"
                : globalCloudValue === undefined
                  ? "Loading…"
                  : globalCloudValue === null
                    ? "Unavailable"
                    : `${Math.round(globalCloudValue)}%`}
            </strong>

            {inspectedWeather && (
              <>
                <span>Pressure</span>
                <strong>{Math.round(inspectedWeather.pressure)} hPa</strong>
              </>
            )}

            <span>Wind (GFS)</span>
            <strong>
              {!globalWindSource
                ? "Unavailable"
                : globalWindValue === undefined
                  ? "Loading…"
                  : globalWindValue === null || globalWindSpeed === null
                    ? "Unavailable"
                    : `${(globalWindSpeed * 3.6).toFixed(1)} km/h`}
            </strong>
            <span>Direction</span>
            <strong>
              {globalWindSpeed !== null && globalWindSpeed < 0.2
                ? "Calm"
                : globalWindDirection === null
                  ? "Unavailable"
                  : formatWindDirection(globalWindDirection)}
            </strong>

            {!inspectedWeather && !globalPrecipitationSource && !globalCloudSource && !globalWindSource && !globalTemperatureSource && (
              <span className="inspector-unavailable">
                Forecast values are outside the current sampled field.
              </span>
            )}
          </div>

          <small>
            {activePrecipitationTimestep
              ? `${accumulationIntervalLabel(activePrecipitationTimestep)} · GFS precipitation`
              : activeCloudTimestep
                ? `${activeCloudTimestep.validTime.replace("T", " ").replace("Z", " UTC")} · GFS cloud cover`
              : activeWindTimestep
                ? `${activeWindTimestep.validTime.replace("T", " ").replace("Z", " UTC")} · GFS 10 m wind`
              : activeTemperatureTimestep
                ? `${activeTemperatureTimestep.validTime.replace("T", " ").replace("Z", " UTC")} · GFS 2 m temperature`
              : inspectionGrid
                ? formatForecastTime(inspectionGrid, localForecastHour)
              : weatherGridStatus === "rate-limited"
                ? "Forecast refresh delayed"
                : weatherGridStatus === "error"
                  ? "Forecast unavailable at this point"
                  : "Forecast field loading"}
            {inspectedWeather
              ? ` · Open-Meteo pressure at ${formatForecastTime(inspectionGrid!, localForecastHour)} · interpolated from ${inspectionGrid?.rows} × ${inspectionGrid?.columns} samples${inspectionGrid !== weatherGrid ? " · cached region" : ""}`
              : ""}
            {globalPrecipitationSource && activePrecipitationTimestep
              ? ` · GFS 0.25° ${activePrecipitationTimestep.accumulationHours} h accumulation · run ${globalPrecipitationSource.manifest.runTime.replace("T", " ").replace(":00:00Z", "Z")}`
              : " · GFS precipitation unavailable; no Open-Meteo fallback"}
            {globalCloudSource && activeCloudTimestep
              ? ` · GFS total cloud cover · run ${globalCloudSource.manifest.runTime.replace("T", " ").replace(":00:00Z", "Z")}`
              : " · GFS cloud unavailable; no Open-Meteo fallback"}
            {globalWindSource && activeWindTimestep
              ? ` · GFS 0.25° 10 m wind · run ${globalWindSource.manifest.runTime.replace("T", " ").replace(":00:00Z", "Z")}`
              : " · GFS wind unavailable; no Open-Meteo fallback"}
            {globalTemperatureSource && activeTemperatureTimestep
              ? ` · GFS 0.25° 2 m temperature · run ${globalTemperatureSource.manifest.runTime.replace("T", " ").replace(":00:00Z", "Z")}`
              : " · GFS temperature unavailable; no Open-Meteo fallback"}
          </small>
        </div>
      )}
    </div>
  );
}
