import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";

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
import { getScalarTimestep } from "../services/globalWeatherService";
import { sampleScalarField } from "../services/numericTileCache";
import {
  removePrecipitationSymbols,
  setPrecipitationSymbolEnabled,
  setPrecipitationSymbolCoverage,
} from "../services/precipitationSymbols";
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
  setTemperatureContourCoverage,
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
  removeWeatherSurface,
  setWeatherSurfaceEnabled,
  setWeatherSurfaceCoverage,
  updateWeatherSurface,
} from "../services/weatherSurface";
import {
  removeWindLayer,
  setWindLayerEnabled,
  setWindLayerCoverage,
  updateWindLayer,
} from "../services/windLayer";

import type { Basemap, MapOverlayState } from "../types/layer";
import type {
  GlobalPrecipitationStatus,
  ScalarWeatherFieldSource,
} from "../types/globalWeather";
import type { SatelliteLayerStatus } from "../services/satelliteLayer";
import type { SelectedLocation } from "../types/location";
import type {
  WeatherGrid,
  WeatherGridRequest,
  WeatherGridStatus,
} from "../types/weatherGrid";

import "maplibre-gl/dist/maplibre-gl.css";

interface MapViewProps {
  selectedLocation: SelectedLocation | null;
  basemap: Basemap;
  mapOverlays: MapOverlayState;
  weatherGrid: WeatherGrid | null;
  weatherGridHistory: WeatherGrid[];
  weatherGridStatus: WeatherGridStatus;
  globalPrecipitationSource: ScalarWeatherFieldSource | null;
  globalPrecipitationStatus: GlobalPrecipitationStatus;
  forecastHour: number;
  localForecastHour: number;
  panelCollapsed: boolean;
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

const BASEMAP_NAMES: Record<Basemap, string> = {
  terrain: "Terrain",
  satellite: "Satellite",
};

function removeForecastVisualizations(map: maplibregl.Map): void {
  removeWeatherSurface(map);
  removeGlobalPrecipitationLayer(map);
  removeTemperatureContourLayer(map);
  removePressureLayer(map);
  removeWindLayer(map);
  removePrecipitationSymbols(map);
}

function renderVisualizations(
  map: maplibregl.Map,
  basemap: Basemap,
  overlays: MapOverlayState,
  grid: WeatherGrid | null,
  globalPrecipitationSource: ScalarWeatherFieldSource | null,
  forecastHour: number,
  localForecastHour: number
): void {
  if (!map.isStyleLoaded()) return;

  applySatelliteLayerState(map, basemap === "satellite");
  applyTerrainLayerState(map, basemap, overlays.elevation);

  if (overlays.clouds && grid) {
    updateWeatherSurface(map, "clouds", grid, localForecastHour);
  } else {
    setWeatherSurfaceEnabled(map, "clouds", false);
  }

  if (overlays.precipitation && globalPrecipitationSource) {
    updateGlobalPrecipitationLayer(
      map,
      globalPrecipitationSource,
      getScalarTimestep(globalPrecipitationSource, forecastHour)
    );
    setWeatherSurfaceEnabled(map, "precipitation", false);
    setPrecipitationSymbolEnabled(map, false);
  } else {
    setGlobalPrecipitationEnabled(map, false);
    setWeatherSurfaceEnabled(map, "precipitation", false);
    setPrecipitationSymbolEnabled(map, false);
  }

  if (overlays.temperatureContours && grid) {
    updateTemperatureContourLayer(map, grid, localForecastHour);
  } else {
    setTemperatureContourEnabled(map, false);
  }

  if (overlays.pressureIsobars && grid) {
    updatePressureLayer(map, grid, localForecastHour);
  } else {
    setPressureLayerEnabled(map, false);
  }

  if (overlays.windFlow && grid) {
    updateWindLayer(map, grid, localForecastHour, basemap);
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
  basemap,
  mapOverlays,
  weatherGrid,
  weatherGridHistory,
  weatherGridStatus,
  globalPrecipitationSource,
  globalPrecipitationStatus,
  forecastHour,
  localForecastHour,
  panelCollapsed,
  onLocationSelect,
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

  const mapContainer = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null);
  const requestTimeoutRef = useRef<number | null>(null);
  const queueWeatherRequestRef = useRef<() => void>(() => undefined);
  const syncSatelliteViewRef = useRef<() => void>(() => undefined);

  const weatherGridRef = useRef<WeatherGrid | null>(weatherGrid);
  const globalPrecipitationSourceRef = useRef(globalPrecipitationSource);
  const basemapRef = useRef(basemap);
  const mapOverlaysRef = useRef(mapOverlays);
  const forecastHourRef = useRef(forecastHour);
  const localForecastHourRef = useRef(localForecastHour);
  const locationSelectRef = useRef(onLocationSelect);
  const weatherGridRequestRef = useRef(onWeatherGridRequest);
  const activeInspection = hoverInspection ?? selectedInspection;
  const activeGlobalTimestep = globalPrecipitationSource
    ? getScalarTimestep(globalPrecipitationSource, forecastHour)
    : null;

  useEffect(() => {
    weatherGridRef.current = weatherGrid;
  }, [weatherGrid]);

  useEffect(() => {
    globalPrecipitationSourceRef.current = globalPrecipitationSource;
  }, [globalPrecipitationSource]);

  useEffect(() => {
    basemapRef.current = basemap;
  }, [basemap]);

  useEffect(() => {
    mapOverlaysRef.current = mapOverlays;
  }, [mapOverlays]);

  useEffect(() => {
    forecastHourRef.current = forecastHour;
  }, [forecastHour]);

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
    if (
      !activeInspection ||
      !mapOverlays.precipitation ||
      !globalPrecipitationSource ||
      !activeGlobalTimestep
    ) {
      return;
    }

    let isCurrent = true;
    const key = [
      activeGlobalTimestep.id,
      activeInspection.longitude.toFixed(5),
      activeInspection.latitude.toFixed(5),
    ].join(":");
    const timeout = window.setTimeout(() => {
      sampleScalarField(
        globalPrecipitationSource,
        activeGlobalTimestep,
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
    }, 80);

    return () => {
      isCurrent = false;
      window.clearTimeout(timeout);
    };
  }, [
    activeInspection,
    activeGlobalTimestep,
    globalPrecipitationSource,
    mapOverlays.precipitation,
  ]);

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
            forecastHourRef.current,
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
        forecastHourRef.current,
        localForecastHourRef.current
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
      captureSatelliteBasemapLayers(map);
      configurePlanetAndTerrain(map);
      renderVisualizations(
        map,
        basemapRef.current,
        mapOverlaysRef.current,
        weatherGridRef.current,
        globalPrecipitationSourceRef.current,
        forecastHourRef.current,
        localForecastHourRef.current
      );
      setForecastCoverage(map, weatherGridRef.current);
      syncSatelliteView();
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
      queueWeatherRequestRef.current = () => undefined;
      syncSatelliteViewRef.current = () => undefined;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;

    if (!map?.isStyleLoaded()) return;

    renderVisualizations(
      map,
      basemap,
      mapOverlays,
      weatherGrid,
      globalPrecipitationSource,
      forecastHour,
      localForecastHour
    );
    setForecastCoverage(map, weatherGrid);
  }, [
    basemap,
    mapOverlays,
    weatherGrid,
    globalPrecipitationSource,
    forecastHour,
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
    activeInspection && activeGlobalTimestep
      ? [
          activeGlobalTimestep.id,
          activeInspection.longitude.toFixed(5),
          activeInspection.latitude.toFixed(5),
        ].join(":")
      : null;
  const globalPrecipitationValue =
    globalPrecipitationSample?.key === expectedGlobalSampleKey
      ? globalPrecipitationSample.value
      : undefined;
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
  const globalPrecipitationStatusText =
    !mapOverlays.precipitation
      ? ""
      : globalPrecipitationStatus === "loading"
        ? " · GFS loading"
        : globalPrecipitationStatus === "ready"
          ? " · GFS 0.25°"
          : " · GFS unavailable";
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
          {globalPrecipitationStatusText}
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

            {inspectedWeather && (
              <>
                <span>Temperature</span>
                <strong>{inspectedWeather.temperature.toFixed(1)} °C</strong>
              </>
            )}

            {(inspectedWeather || mapOverlays.precipitation) && (
              <>
                <span>Precipitation{mapOverlays.precipitation ? " (GFS)" : ""}</span>
                <strong>{mapOverlays.precipitation
                  ? !globalPrecipitationSource
                    ? "Unavailable"
                    : globalPrecipitationValue === undefined
                    ? "Loading…"
                    : globalPrecipitationValue === null
                      ? "Unavailable"
                      : globalPrecipitationValue < 0.05
                        ? "Dry"
                        : `${globalPrecipitationValue.toFixed(2)} mm`
                  : inspectedWeather!.precipitation < 0.05
                    ? "Dry"
                    : `${inspectedWeather!.precipitation.toFixed(1)} mm`}</strong>
              </>
            )}

            {inspectedWeather && (
              <>
                <span>Cloud cover</span>
                <strong>≈ {Math.round(inspectedWeather.cloudCover / 5) * 5}%</strong>
                <span>Pressure</span>
                <strong>{Math.round(inspectedWeather.pressure)} hPa</strong>
                <span>Wind</span>
                <strong>{Math.round(inspectedWeather.windSpeed)} km/h</strong>
                <span>Direction</span>
                <strong>{formatWindDirection(inspectedWeather.windDirection)}</strong>
              </>
            )}

            {!inspectedWeather && !mapOverlays.precipitation && (
              <span className="inspector-unavailable">
                Forecast values are outside the current sampled field.
              </span>
            )}
          </div>

          <small>
            {mapOverlays.precipitation && activeGlobalTimestep
              ? `${activeGlobalTimestep.validTime.replace("T", " ").replace("Z", " UTC")} · GFS precipitation`
              : inspectionGrid
                ? formatForecastTime(inspectionGrid, localForecastHour)
              : weatherGridStatus === "rate-limited"
                ? "Forecast refresh delayed"
                : weatherGridStatus === "error"
                  ? "Forecast unavailable at this point"
                  : "Forecast field loading"}
            {inspectedWeather
              ? ` · Open-Meteo variables at ${formatForecastTime(inspectionGrid!, localForecastHour)} · interpolated from ${inspectionGrid?.rows} × ${inspectionGrid?.columns} samples${inspectionGrid !== weatherGrid ? " · cached region" : ""}`
              : ""}
            {mapOverlays.precipitation && globalPrecipitationSource && activeGlobalTimestep
              ? ` · GFS 0.25° ${activeGlobalTimestep.accumulationHours} h accumulation`
              : mapOverlays.precipitation
                ? " · GFS precipitation unavailable; no Open-Meteo fallback"
              : ""}
          </small>
        </div>
      )}
    </div>
  );
}
