import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import { accumulationIntervalLabel } from "../../weather/presentation/weatherTimeLabel";
import { precipitationAmountLabel } from "../../weather/presentation/precipitationStyle";

import { NOMINATIM_ATTRIBUTION } from "../../atlas/map/atlasAttribution";
import { OPEN_METEO_ATTRIBUTION } from "../../weather/map/weatherAttribution";
import {
  IS_SATELLITE_CONFIGURED,
  SATELLITE_PROVIDER,
} from "../../atlas/map/satelliteProvider";
import { AtlasMap } from "../../atlas/map/AtlasMap";
import {
  TERRAIN_EXAGGERATION,
  TERRAIN_MIN_ZOOM,
} from "../../atlas/map/terrainLayers";
import { WeatherMapController } from "../../weather/map/WeatherMapController";
import { useWeatherMapInspection } from "../../weather/map/useWeatherMapInspection";
import { formatWindDirection } from "../../weather/map/windVector";
import { TraverseMapController } from "../../traverse/map/TraverseMapController";
import {
  calculateRouteFitPadding,
  DEFAULT_WORKSPACE_GUTTER_PX,
} from "../../traverse/map/routeCamera";

import type { Basemap } from "../../atlas/map/mapTypes";
import type { MapOverlayState } from "../state/mapOverlayState";
import type {
  GlobalWeatherStatusRegistry,
  ScalarWeatherFieldSource,
  VectorWeatherFieldSource,
} from "../../weather/types/globalWeather";
import type { SatelliteLayerStatus } from "../../atlas/map/satelliteLayer";
import type { SelectedLocation } from "../../atlas/location/location";
import type {
  ResampledRouteGeometry,
  RouteCoordinate,
  TerrainRoute,
} from "../../traverse/types/route";
import type {
  RouteConditionMode,
  RouteConditions,
} from "../../traverse/types/routeConditions";

import "maplibre-gl/dist/maplibre-gl.css";
interface MeridianMapProps {
  selectedLocation: SelectedLocation | null;
  basemap: Basemap;
  mapOverlays: MapOverlayState;
  globalPrecipitationSource: ScalarWeatherFieldSource | null;
  globalCloudSource: ScalarWeatherFieldSource | null;
  globalWindSource: VectorWeatherFieldSource | null;
  globalTemperatureSource: ScalarWeatherFieldSource | null;
  globalPressureSource: ScalarWeatherFieldSource | null;
  globalWeatherStatuses: GlobalWeatherStatusRegistry;
  activeGlobalValidTime: string | null;
  routeGeometry: ResampledRouteGeometry | null;
  terrainRoute: TerrainRoute | null;
  focusedRouteSampleIndex: number | null;
  routeConditions: RouteConditions | null;
  routeConditionMode: RouteConditionMode;
  panelCollapsed: boolean;
  mapInspectorEnabled: boolean;
  mapInspectorSession: number;
  onLocationSelect: (location: SelectedLocation) => void;
  onRouteSampleFocus: (index: number | null) => void;
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
  inspectorSession: number;
}

const BASEMAP_NAMES: Record<Basemap, string> = {
  terrain: "Terrain",
  satellite: "Satellite",
};

function createInspectionPoint(
  map: maplibregl.Map,
  location: maplibregl.LngLatLike,
  x: number,
  y: number,
  persistent: boolean,
  inspectorSession: number
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
    inspectorSession,
  };
}

function formatElevation(elevation: number | null): string {
  return elevation === null ? "Unavailable" : `≈ ${Math.round(elevation / 10) * 10} m`;
}

export default function MeridianMap({
  selectedLocation,
  basemap,
  mapOverlays,
  globalPrecipitationSource,
  globalCloudSource,
  globalWindSource,
  globalTemperatureSource,
  globalPressureSource,
  globalWeatherStatuses,
  activeGlobalValidTime,
  routeGeometry,
  terrainRoute,
  focusedRouteSampleIndex,
  routeConditions,
  routeConditionMode,
  panelCollapsed,
  mapInspectorEnabled,
  mapInspectorSession,
  onLocationSelect,
  onRouteSampleFocus,
}: MeridianMapProps) {
  const [hoverInspection, setHoverInspection] =
    useState<InspectionPoint | null>(null);
  const [selectedInspection, setSelectedInspection] =
    useState<InspectionPoint | null>(null);
  const [satelliteStatus, setSatelliteStatus] = useState<SatelliteLayerStatus>(
    IS_SATELLITE_CONFIGURED ? "idle" : "unavailable"
  );

  const mapContainer = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const styleReadyRef = useRef(false);
  const markerRef = useRef<maplibregl.Marker | null>(null);
  const atlasMapRef = useRef<AtlasMap | null>(null);
  const weatherMapControllerRef = useRef<WeatherMapController | null>(null);
  const traverseMapControllerRef = useRef<TraverseMapController | null>(null);

  const globalPrecipitationSourceRef = useRef(globalPrecipitationSource);
  const globalCloudSourceRef = useRef(globalCloudSource);
  const globalWindSourceRef = useRef(globalWindSource);
  const globalTemperatureSourceRef = useRef(globalTemperatureSource);
  const globalPressureSourceRef = useRef(globalPressureSource);
  const basemapRef = useRef(basemap);
  const mapOverlaysRef = useRef(mapOverlays);
  const activeGlobalValidTimeRef = useRef(activeGlobalValidTime);
  const locationSelectRef = useRef(onLocationSelect);
  const routeCoordinatesRef = useRef<RouteCoordinate[]>([]);
  const routeFocusRef = useRef(onRouteSampleFocus);
  const focusedRouteSampleRef = useRef(focusedRouteSampleIndex);
  const routeConditionsRef = useRef(routeConditions);
  const routeConditionModeRef = useRef(routeConditionMode);
  const mapInspectorEnabledRef = useRef(mapInspectorEnabled);
  const mapInspectorSessionRef = useRef(mapInspectorSession);
  const fittedRouteIdRef = useRef<string | null>(null);
  const candidateInspection = hoverInspection ?? selectedInspection;
  const activeInspection = mapInspectorEnabled &&
    candidateInspection?.inspectorSession === mapInspectorSession
      ? candidateInspection
      : null;
  const {
    precipitationTimestep: activePrecipitationTimestep,
    cloudTimestep: activeCloudTimestep,
    windTimestep: activeWindTimestep,
    temperatureTimestep: activeTemperatureTimestep,
    pressureTimestep: activePressureTimestep,
    precipitationValue: globalPrecipitationValue,
    cloudValue: globalCloudValue,
    windValue: globalWindValue,
    temperatureValue: globalTemperatureValue,
    pressureValue: globalPressureValue,
  } = useWeatherMapInspection({
    point: activeInspection,
    validTime: activeGlobalValidTime,
    precipitation: globalPrecipitationSource,
    clouds: globalCloudSource,
    wind: globalWindSource,
    temperature: globalTemperatureSource,
    pressure: globalPressureSource,
  });
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
    globalPressureSourceRef.current = globalPressureSource;
  }, [globalPressureSource]);

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
    locationSelectRef.current = onLocationSelect;
  }, [onLocationSelect]);

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

  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

    let weatherController: WeatherMapController | null = null;
    let traverseController: TraverseMapController | null = null;
    let refreshSelectedElevation = () => undefined;
    const atlasMap = new AtlasMap(mapContainer.current, {
      attributions: [OPEN_METEO_ATTRIBUTION, NOMINATIM_ATTRIBUTION],
      onStyleReady: () => {
        styleReadyRef.current = true;
        mapContainer.current?.setAttribute("data-map-style-ready", "true");
        traverseController?.styleChanged();
        weatherController?.styleChanged();
      },
      onRenderable: () => {
        weatherController?.mapBecameRenderable();
        refreshSelectedElevation();
      },
      onSatelliteStatus: setSatelliteStatus,
    });
    const map = atlasMap.map;
    atlasMapRef.current = atlasMap;
    mapRef.current = map;
    weatherController = new WeatherMapController(map, () => {
      traverseController?.placeAboveWeather();
    });
    traverseController = new TraverseMapController(map);
    weatherMapControllerRef.current = weatherController;
    traverseMapControllerRef.current = traverseController;
    atlasMap.setPresentation(basemapRef.current, mapOverlaysRef.current.elevation);
    weatherController.update({
      basemap: basemapRef.current,
      overlays: mapOverlaysRef.current,
      precipitation: globalPrecipitationSourceRef.current,
      clouds: globalCloudSourceRef.current,
      wind: globalWindSourceRef.current,
      temperature: globalTemperatureSourceRef.current,
      pressure: globalPressureSourceRef.current,
      validTime: activeGlobalValidTimeRef.current,
    });
    traverseController.update({
      coordinates: routeCoordinatesRef.current,
      focusedSampleIndex: focusedRouteSampleRef.current,
      conditions: routeConditionsRef.current,
      conditionMode: routeConditionModeRef.current,
    });

    let pendingPointerEvent: maplibregl.MapMouseEvent | null = null;
    let pointerFrame: number | null = null;

    const handlePointerFrame = () => {
      pointerFrame = null;
      const event = pendingPointerEvent;
      if (!event) return;
      const routeIndex =
        traverseController?.isRouteHit(event.point)
          ? traverseController.nearestSample(event.point, 10)
          : null;
      if (routeIndex !== null && routeIndex !== undefined) {
        routeFocusRef.current(routeIndex);
        setHoverInspection(null);
        return;
      }
      if (!mapInspectorEnabledRef.current) {
        setHoverInspection(null);
        return;
      }
      setHoverInspection(
        createInspectionPoint(
          map,
          event.lngLat,
          event.point.x,
          event.point.y,
          false,
          mapInspectorSessionRef.current
        )
      );
    };

    refreshSelectedElevation = () => {
      const markerLocation = markerRef.current?.getLngLat();
      if (!markerLocation) return;
      const renderedElevation = map.queryTerrainElevation(markerLocation);
      if (renderedElevation === null) return;
      setSelectedInspection((current) =>
        current
          ? { ...current, elevation: renderedElevation / TERRAIN_EXAGGERATION }
          : current
      );
    };

    const handleMouseMove = (event: maplibregl.MapMouseEvent) => {
      pendingPointerEvent = event;
      if (pointerFrame === null) {
        pointerFrame = window.requestAnimationFrame(handlePointerFrame);
      }
    };

    map.on("moveend", () => weatherController?.viewportChanged());
    map.on("movestart", () => setHoverInspection(null));
    map.on("mousemove", handleMouseMove);
    map.on("mouseleave", () => setHoverInspection(null));
    map.on("click", (event) => {
      const routeIndex = traverseController?.nearestSample(event.point) ?? null;
      if (routeIndex !== null) {
        setHoverInspection(null);
        setSelectedInspection(null);
        routeFocusRef.current(routeIndex);
        return;
      }
      setHoverInspection(null);
      setSelectedInspection(
        mapInspectorEnabledRef.current
          ? createInspectionPoint(
              map,
              event.lngLat,
              event.point.x,
              event.point.y,
              true,
              mapInspectorSessionRef.current
            )
          : null
      );
      locationSelectRef.current({
        latitude: event.lngLat.lat,
        longitude: event.lngLat.lng,
      });
    });

    return () => {
      if (pointerFrame !== null) window.cancelAnimationFrame(pointerFrame);
      markerRef.current?.remove();
      markerRef.current = null;
      weatherController?.destroy();
      traverseController?.destroy();
      atlasMap.destroy();
      atlasMapRef.current = null;
      weatherMapControllerRef.current = null;
      traverseMapControllerRef.current = null;
      mapRef.current = null;
      styleReadyRef.current = false;
    };
  }, []);

  useEffect(() => {
    mapInspectorEnabledRef.current = mapInspectorEnabled;
    mapInspectorSessionRef.current = mapInspectorSession;
  }, [mapInspectorEnabled, mapInspectorSession]);

  useEffect(() => {
    const map = mapRef.current;
    const controller = traverseMapControllerRef.current;
    const coordinates =
      terrainRoute && routeGeometry && terrainRoute.id === routeGeometry.id
        ? terrainRoute.samples
        : routeGeometry?.coordinates ?? [];
    routeCoordinatesRef.current = coordinates;

    if (!routeGeometry) {
      fittedRouteIdRef.current = null;
    } else if (map && controller && fittedRouteIdRef.current !== routeGeometry.id) {
      fittedRouteIdRef.current = routeGeometry.id;
      const mapBounds = mapContainer.current?.getBoundingClientRect();
      const shell = mapContainer.current?.closest<HTMLElement>(".desktop-shell-active");
      const workspaces = panelCollapsed
        ? []
        : [...(shell?.querySelectorAll<HTMLElement>(".desktop-workspace, .detail-workspace") ?? [])];
      const workspaceRight = workspaces.reduce<number | null>(
        (right, workspace) =>
          Math.max(
            right ?? Number.NEGATIVE_INFINITY,
            workspace.getBoundingClientRect().right
          ),
        null
      );
      const configuredGutter = shell
        ? Number.parseFloat(
            getComputedStyle(shell).getPropertyValue("--workspace-gutter")
          )
        : Number.NaN;
      const padding = shell
        ? calculateRouteFitPadding({
            mapLeftPx: mapBounds?.left ?? 0,
            workspaceRightPx: workspaceRight,
            workspaceGutterPx: Number.isFinite(configuredGutter)
              ? configuredGutter
              : DEFAULT_WORKSPACE_GUTTER_PX,
          })
        : {
            top: 70,
            right: 70,
            bottom: 70,
            left: panelCollapsed ? 70 : 410,
          };
      controller.fitRoute(routeGeometry.coordinates, padding);
    }

    controller?.update({
      coordinates,
      focusedSampleIndex: focusedRouteSampleIndex,
      conditions: routeConditions,
      conditionMode: routeConditionMode,
    });
  }, [
    focusedRouteSampleIndex,
    panelCollapsed,
    routeConditionMode,
    routeConditions,
    routeGeometry,
    terrainRoute,
  ]);
  useEffect(() => {
    atlasMapRef.current?.setPresentation(basemap, mapOverlays.elevation);
    weatherMapControllerRef.current?.update({
      basemap,
      overlays: mapOverlays,
      precipitation: globalPrecipitationSource,
      clouds: globalCloudSource,
      wind: globalWindSource,
      temperature: globalTemperatureSource,
      pressure: globalPressureSource,
      validTime: activeGlobalValidTime,
    });
  }, [
    basemap,
    mapOverlays,
    globalPrecipitationSource,
    globalCloudSource,
    globalWindSource,
    globalTemperatureSource,
    globalPressureSource,
    activeGlobalValidTime,
  ]);
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    atlasMapRef.current?.resize();
    const resizeTimer = window.setTimeout(() => atlasMapRef.current?.resize(), 240);
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
      mapInspectorEnabledRef.current
        ? createInspectionPoint(
            map,
            lngLat,
            container.clientWidth / 2,
            container.clientHeight / 2,
            true,
            mapInspectorSessionRef.current
          )
        : null
    );
  }, [selectedLocation]);

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
    mapOverlays.pressureIsobars ? globalWeatherStatuses.pressure_msl : null,
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

            <span>Pressure (GFS)</span>
            <strong>
              {!globalPressureSource
                ? "Unavailable"
                : globalPressureValue === undefined
                  ? "Loading…"
                  : globalPressureValue === null
                    ? "Unavailable"
                    : `${globalPressureValue.toFixed(1)} hPa`}
            </strong>

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

            {!globalPrecipitationSource && !globalCloudSource && !globalWindSource && !globalTemperatureSource && !globalPressureSource && (
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
              : activePressureTimestep
                ? `${activePressureTimestep.validTime.replace("T", " ").replace("Z", " UTC")} · GFS mean sea-level pressure`
                : "Forecast field loading"}
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
            {globalPressureSource && activePressureTimestep
              ? ` · GFS 0.25° mean sea-level pressure · run ${globalPressureSource.manifest.runTime.replace("T", " ").replace(":00:00Z", "Z")}`
              : " · GFS pressure unavailable; no Open-Meteo fallback"}
          </small>
        </div>
      )}
    </div>
  );
}
