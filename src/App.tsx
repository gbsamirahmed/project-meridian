import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import MapView from "./components/MapView";
import WeatherPanel from "./components/WeatherPanel";
import RoutePlannerPanel from "./components/RoutePlannerPanel";

import { getWeather } from "./services/weatherService";
import { getLocationName } from "./services/locationService";
import { searchLocation } from "./services/searchService";
import {
  intersectScalarValidTimes,
  loadGlobalWeatherSources,
} from "./services/globalWeatherService";
import {
  catalogueForecastIndex,
  GlobalWeatherCatalogueWatcher,
  type CatalogueCheckState,
} from "./services/weatherCatalogueRefresh";
import { IS_SATELLITE_CONFIGURED } from "./config/satelliteProvider";
import {
  MAX_GPX_FILE_BYTES,
  parseGpxText,
  resampleRouteGeometry,
} from "./services/routeGeometry";
import { sampleTerrainElevations } from "./services/terrainElevationSampler";
import { buildTerrainRoute } from "./services/routeTerrain";
import {
  buildJourneySchedule,
  DEFAULT_JOURNEY_PROFILE,
} from "./services/journeyModel";
import { buildRouteConditions } from "./services/routeConditions";
import {
  getWeatherGrid,
  getWeatherGridRequestKey,
  WeatherGridHttpError,
} from "./services/gridWeatherService";

import type { SelectedLocation } from "./types/location";
import type { WeatherData } from "./types/weather";
import type { Place } from "./types/place";
import type { Basemap, MapOverlayState } from "./types/layer";
import type {
  GlobalWeatherCatalog,
  GlobalWeatherSourceRegistry,
  GlobalWeatherStatusRegistry,
  GlobalWeatherFieldSource,
} from "./types/globalWeather";
import type {
  WeatherGrid,
  WeatherGridRequest,
  WeatherGridStatus,
} from "./types/weatherGrid";
import type {
  JourneyPlan,
  JourneyProfile,
  JourneySchedule,
  ResampledRouteGeometry,
  RoutePreparationStatus,
  TerrainRoute,
} from "./types/route";
import type {
  RouteConditionMode,
  RouteConditions,
  RouteConditionStatus,
} from "./types/routeConditions";

import "./App.css";

function timestamp(time: string): number {
  return Date.parse(/(?:Z|[+-]\d{2}:?\d{2})$/.test(time) ? time : `${time}Z`);
}

function closestForecastIndex(times: string[], targetTime: string): number {
  const target = timestamp(targetTime);
  let bestIndex = 0;
  let bestDifference = Number.POSITIVE_INFINITY;
  times.forEach((time, index) => {
    const difference = Math.abs(timestamp(time) - target);
    if (difference < bestDifference) {
      bestDifference = difference;
      bestIndex = index;
    }
  });
  return bestIndex;
}

function futureIso(hours: number): string {
  const date = new Date(Date.now() + hours * 3600000);
  date.setMinutes(Math.ceil(date.getMinutes() / 15) * 15, 0, 0);
  return date.toISOString();
}

function App() {
  const [selectedLocation, setSelectedLocation] =
    useState<SelectedLocation | null>(null);
  const [debouncedLocation, setDebouncedLocation] =
    useState<SelectedLocation | null>(null);
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [place, setPlace] = useState<Place | null>(null);
  const [basemap, setBasemap] = useState<Basemap>("terrain");
  const [mapOverlays, setMapOverlays] = useState<MapOverlayState>({
      elevation: false,
      precipitation: false,
      clouds: false,
      temperatureContours: false,
      pressureIsobars: false,
      windFlow: false,
    });
  const [weatherGrid, setWeatherGrid] =
    useState<WeatherGrid | null>(null);
  const [weatherGridHistory, setWeatherGridHistory] = useState<
    WeatherGrid[]
  >([]);
  const [weatherGridStatus, setWeatherGridStatus] =
    useState<WeatherGridStatus>("idle");
  const [forecastHour, setForecastHour] = useState(0);
  const [globalWeatherCatalog, setGlobalWeatherCatalog] =
    useState<GlobalWeatherCatalog | null>(null);
  const [catalogueCheck, setCatalogueCheck] = useState<CatalogueCheckState>({
    lastSuccessfulCheck: null,
    lastCheckFailed: false,
  });
  const [globalWeatherSources, setGlobalWeatherSources] =
    useState<GlobalWeatherSourceRegistry>({});
  const [globalWeatherStatuses, setGlobalWeatherStatuses] =
    useState<GlobalWeatherStatusRegistry>({
      precipitation: "loading",
      cloud_cover: "loading",
      wind_10m: "loading",
      temperature_2m: "loading",
      gust_surface: "loading",
      visibility_surface: "loading",
      freezing_level: "loading",
      highest_freezing_level: "loading",
      cloud_ceiling: "loading",
    });
  const [isDesktopPanelCollapsed, setIsDesktopPanelCollapsed] =
    useState(false);
  const [routeGeometry, setRouteGeometry] =
    useState<ResampledRouteGeometry | null>(null);
  const [terrainRoute, setTerrainRoute] = useState<TerrainRoute | null>(null);
  const [routeStatus, setRouteStatus] =
    useState<RoutePreparationStatus>("idle");
  const [routeStatusMessage, setRouteStatusMessage] = useState<string | null>(null);
  const [journeyProfile, setJourneyProfile] = useState<JourneyProfile>(
    DEFAULT_JOURNEY_PROFILE
  );
  const [journeyPlan, setJourneyPlan] = useState<JourneyPlan>(() => ({
    mode: "profile",
    departureTime: futureIso(1),
    targetDurationMinutes: 360,
    targetFinishTime: futureIso(7),
  }));
  const [focusedRouteSampleIndex, setFocusedRouteSampleIndex] = useState<
    number | null
  >(null);
  const [routeConditions, setRouteConditions] =
    useState<RouteConditions | null>(null);
  const [routeConditionStatus, setRouteConditionStatus] =
    useState<RouteConditionStatus>("idle");
  const [routeConditionMode, setRouteConditionMode] =
    useState<RouteConditionMode>("none");

  const weatherGridAbortRef = useRef<AbortController | null>(null);
  const locationNameAbortRef = useRef<AbortController | null>(null);
  const searchAbortRef = useRef<AbortController | null>(null);
  const weatherGridRequestIdRef = useRef(0);
  const activeWeatherRequestKeyRef = useRef<string | null>(null);
  const latestWeatherRequestRef = useRef<WeatherGridRequest | null>(null);
  const weatherGridRef = useRef<WeatherGrid | null>(null);
  const weatherGridRetryTimerRef = useRef<number | null>(null);
  const weatherGridRetryCountRef = useRef(0);
  const weatherGridRetryKeyRef = useRef<string | null>(null);
  const weatherGridCooldownUntilRef = useRef(0);
  const hasInitialisedGfsTimelineRef = useRef(false);
  const activeGlobalValidTimeRef = useRef<string | null>(null);
  const mapOverlaysRef = useRef(mapOverlays);
  const routeAbortRef = useRef<AbortController | null>(null);
  const routeGenerationRef = useRef(0);
  const routeConditionAbortRef = useRef<AbortController | null>(null);
  const routeConditionGenerationRef = useRef(0);
  const runWeatherGridRequestRef = useRef<
    (request: WeatherGridRequest) => void
  >(() => undefined);

  useEffect(() => {
    let isCurrent = true;
    let watcher: GlobalWeatherCatalogueWatcher | null = null;
    const updateCheck = (next: CatalogueCheckState) => {
      if (!isCurrent) return;
      setCatalogueCheck((current) => ({
        lastSuccessfulCheck:
          next.lastSuccessfulCheck ?? current.lastSuccessfulCheck,
        lastCheckFailed: next.lastCheckFailed,
      }));
    };
    const adopt = (result: {
      catalog: GlobalWeatherCatalog;
      sources: GlobalWeatherSourceRegistry;
      statuses: GlobalWeatherStatusRegistry;
    }) => {
      if (!isCurrent) return;
      const globalOverlayActive =
        mapOverlaysRef.current.precipitation ||
        mapOverlaysRef.current.clouds ||
        mapOverlaysRef.current.windFlow ||
        mapOverlaysRef.current.temperatureContours;
      if (globalOverlayActive && result.sources.precipitation) {
        const times = result.sources.precipitation.manifest.timesteps.map(
          (step) => step.validTime
        );
        setForecastHour(
          catalogueForecastIndex(times, activeGlobalValidTimeRef.current)
        );
      }
      setGlobalWeatherCatalog(result.catalog);
      setGlobalWeatherSources(result.sources);
      setGlobalWeatherStatuses(result.statuses);
    };

    loadGlobalWeatherSources()
      .then((result) => {
        if (!isCurrent) return;
        if (result.catalog) {
          adopt({
            catalog: result.catalog,
            sources: result.sources,
            statuses: result.statuses,
          });
        } else {
          setGlobalWeatherSources(result.sources);
          setGlobalWeatherStatuses(result.statuses);
          setGlobalWeatherCatalog(null);
        }
        updateCheck({
          lastSuccessfulCheck: result.catalog ? new Date().toISOString() : null,
          lastCheckFailed: !result.catalog,
        });
        const completeInitialRun =
          result.catalog &&
          Object.values(result.statuses).every((status) => status === "ready");
        watcher = new GlobalWeatherCatalogueWatcher(
          completeInitialRun ? result.catalog : null,
          adopt,
          updateCheck,
          { visibility: document }
        );
        watcher.start();
      })
      .catch(() => {
        if (!isCurrent) return;
        updateCheck({ lastSuccessfulCheck: null, lastCheckFailed: true });
        watcher = new GlobalWeatherCatalogueWatcher(null, adopt, updateCheck, {
          visibility: document,
        });
        watcher.start();
      });

    return () => {
      isCurrent = false;
      watcher?.stop();
    };
  }, []);

  const globalPrecipitationSource = globalWeatherSources.precipitation ?? null;
  const globalCloudSource = globalWeatherSources.cloud_cover ?? null;
  const globalWindSource = globalWeatherSources.wind_10m ?? null;
  const globalTemperatureSource = globalWeatherSources.temperature_2m ?? null;
  const activeGlobalSources = [
    mapOverlays.precipitation ? globalPrecipitationSource : null,
    mapOverlays.clouds ? globalCloudSource : null,
    mapOverlays.windFlow ? globalWindSource : null,
    mapOverlays.temperatureContours ? globalTemperatureSource : null,
  ].filter((source): source is GlobalWeatherFieldSource => source !== null);
  const globalForecastTimes = intersectScalarValidTimes(activeGlobalSources);
  const forecastTimes = activeGlobalSources.length
    ? globalForecastTimes
    : weather?.forecastTimes ?? weatherGrid?.times ?? [];
  const forecastHours = activeGlobalSources.length
    ? forecastTimes.map(
        (validTime) =>
          activeGlobalSources[0].manifest.timesteps.find(
            (step) => step.validTime === validTime
          )?.forecastHour ?? 0
      )
    : undefined;
  const activeForecastHour = Math.min(
    forecastHour,
    Math.max(0, forecastTimes.length - 1)
  );
  const activeGlobalValidTime = activeGlobalSources.length
    ? forecastTimes[activeForecastHour] ?? null
    : null;
  const localForecastHour =
    activeGlobalValidTime && weatherGrid?.times.length
      ? closestForecastIndex(weatherGrid.times, activeGlobalValidTime)
      : activeForecastHour;

  useEffect(() => {
    activeGlobalValidTimeRef.current = activeGlobalValidTime;
    mapOverlaysRef.current = mapOverlays;
  }, [activeGlobalValidTime, mapOverlays]);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      setDebouncedLocation(selectedLocation);
    }, 500);

    return () => window.clearTimeout(timeoutId);
  }, [selectedLocation]);

  useEffect(() => {
    if (!debouncedLocation) return;

    let isCurrent = true;
    locationNameAbortRef.current?.abort();
    const locationNameController = new AbortController();
    locationNameAbortRef.current = locationNameController;

    getWeather(
      debouncedLocation.latitude,
      debouncedLocation.longitude
    )
      .then((nextWeather) => {
        if (isCurrent) setWeather(nextWeather);
      })
      .catch((error: unknown) => {
        if (isCurrent) console.error(error);
      });

    getLocationName(
      debouncedLocation.latitude,
      debouncedLocation.longitude,
      locationNameController.signal
    )
      .then((name) => {
        if (isCurrent) setPlace({ name });
      })
      .catch((error: unknown) => {
        if (isCurrent && !locationNameController.signal.aborted) {
          console.error(error);
        }
      });

    return () => {
      isCurrent = false;
      locationNameController.abort();
    };
  }, [debouncedLocation]);

  useEffect(() => {
    return () => {
      weatherGridAbortRef.current?.abort();
      locationNameAbortRef.current?.abort();
      searchAbortRef.current?.abort();
      routeAbortRef.current?.abort();
      routeConditionAbortRef.current?.abort();
      if (weatherGridRetryTimerRef.current !== null) {
        window.clearTimeout(weatherGridRetryTimerRef.current);
      }
    };
  }, []);

  const journeyResult = useMemo<{
    schedule: JourneySchedule | null;
    error: string | null;
  }>(() => {
    if (!terrainRoute) return { schedule: null, error: null };
    try {
      return {
        schedule: buildJourneySchedule(terrainRoute, journeyProfile, journeyPlan),
        error: null,
      };
    } catch (error) {
      return {
        schedule: null,
        error: error instanceof Error ? error.message : "Journey timing is unavailable.",
      };
    }
  }, [journeyPlan, journeyProfile, terrainRoute]);

  useEffect(() => {
    const schedule = journeyResult.schedule;
    const generation = ++routeConditionGenerationRef.current;
    routeConditionAbortRef.current?.abort();
    if (!terrainRoute || !schedule) {
      return;
    }
    const controller = new AbortController();
    routeConditionAbortRef.current = controller;
    queueMicrotask(() => {
      if (
        !controller.signal.aborted &&
        generation === routeConditionGenerationRef.current
      ) {
        setRouteConditionStatus("loading");
      }
    });
    buildRouteConditions(
      terrainRoute,
      schedule,
      {
        temperature: globalTemperatureSource,
        precipitation: globalPrecipitationSource,
        cloud: globalCloudSource,
        wind: globalWindSource,
        gust: globalWeatherSources.gust_surface,
        visibility: globalWeatherSources.visibility_surface,
        freezingLevel: globalWeatherSources.freezing_level,
        highestFreezingLevel: globalWeatherSources.highest_freezing_level,
        cloudCeiling: globalWeatherSources.cloud_ceiling,
      },
      controller.signal
    )
      .then((conditions) => {
        if (
          controller.signal.aborted ||
          generation !== routeConditionGenerationRef.current
        ) {
          return;
        }
        setRouteConditions(conditions);
        const coverages = Object.values(conditions.coverage);
        const available = coverages.reduce(
          (sum, coverage) => sum + coverage.availableSamples,
          0
        );
        const expected = coverages.reduce(
          (sum, coverage) => sum + coverage.totalSamples,
          0
        );
        setRouteConditionStatus(
          available === 0
            ? "unavailable"
            : available === expected
              ? "ready"
              : "partial"
        );
      })
      .catch((error: unknown) => {
        if (
          controller.signal.aborted ||
          generation !== routeConditionGenerationRef.current
        ) {
          return;
        }
        console.error("Route condition preparation failed", error);
        setRouteConditionStatus("unavailable");
      });
    return () => controller.abort();
  }, [
    globalCloudSource,
    globalWeatherSources,
    globalPrecipitationSource,
    globalTemperatureSource,
    globalWindSource,
    journeyResult.schedule,
    terrainRoute,
  ]);

  const scheduleWeatherGridRetry = useCallback((delayMs: number) => {
    if (weatherGridRetryTimerRef.current !== null) {
      window.clearTimeout(weatherGridRetryTimerRef.current);
    }

    weatherGridCooldownUntilRef.current = Date.now() + delayMs;
    weatherGridRetryTimerRef.current = window.setTimeout(() => {
      weatherGridRetryTimerRef.current = null;
      weatherGridCooldownUntilRef.current = 0;

      const latestRequest = latestWeatherRequestRef.current;
      if (latestRequest) runWeatherGridRequestRef.current(latestRequest);
    }, delayMs);
  }, []);

  const runWeatherGridRequest = useCallback(
    (request: WeatherGridRequest) => {
      const requestKey = getWeatherGridRequestKey(request);
      latestWeatherRequestRef.current = request;

      if (activeWeatherRequestKeyRef.current === requestKey) return;

      if (weatherGridRetryKeyRef.current !== requestKey) {
        weatherGridRetryKeyRef.current = requestKey;
        weatherGridRetryCountRef.current = 0;
      }

      const cooldownRemaining =
        weatherGridCooldownUntilRef.current - Date.now();

      if (cooldownRemaining > 0) {
        setWeatherGridStatus("rate-limited");
        scheduleWeatherGridRetry(cooldownRemaining);
        return;
      }

      weatherGridAbortRef.current?.abort();

      const controller = new AbortController();
      const requestId = weatherGridRequestIdRef.current + 1;

      weatherGridAbortRef.current = controller;
      weatherGridRequestIdRef.current = requestId;
      activeWeatherRequestKeyRef.current = requestKey;
      setWeatherGridStatus(weatherGridRef.current ? "refreshing" : "loading");

      getWeatherGrid(request, controller.signal)
        .then((nextGrid) => {
          if (weatherGridRequestIdRef.current !== requestId) return;

          weatherGridRef.current = nextGrid;
          setWeatherGrid(nextGrid);
          setWeatherGridHistory((current) => [
            nextGrid,
            ...current.filter(
              (grid) =>
                grid.fetchedAt !== nextGrid.fetchedAt ||
                grid.bounds.west !== nextGrid.bounds.west ||
                grid.bounds.south !== nextGrid.bounds.south
            ),
          ].slice(0, 8));
          setWeatherGridStatus("ready");
          weatherGridRetryCountRef.current = 0;
          weatherGridCooldownUntilRef.current = 0;
        })
        .catch((error: unknown) => {
          if (controller.signal.aborted) return;
          if (weatherGridRequestIdRef.current !== requestId) return;

          const retryCount = weatherGridRetryCountRef.current + 1;
          weatherGridRetryCountRef.current = retryCount;

          if (error instanceof WeatherGridHttpError && error.status === 429) {
            setWeatherGridStatus("rate-limited");

            const delayMs = Math.min(
              60_000,
              Math.max(error.retryAfterMs ?? 0, 8_000 * 2 ** (retryCount - 1))
            );

            if (retryCount <= 3) scheduleWeatherGridRetry(delayMs);
            else weatherGridCooldownUntilRef.current = Date.now() + delayMs;
            return;
          }

          setWeatherGridStatus("error");

          if (retryCount <= 1) {
            scheduleWeatherGridRetry(6_000);
          } else {
            weatherGridCooldownUntilRef.current = Date.now() + 10_000;
          }
        })
        .finally(() => {
          if (weatherGridRequestIdRef.current === requestId) {
            activeWeatherRequestKeyRef.current = null;
          }
        });
    },
    [scheduleWeatherGridRetry]
  );

  useEffect(() => {
    runWeatherGridRequestRef.current = runWeatherGridRequest;
  }, [runWeatherGridRequest]);

  const handleWeatherGridRequest = useCallback(
    (request: WeatherGridRequest) => {
      runWeatherGridRequestRef.current(request);
    },
    []
  );

  const handleSearch = useCallback(async (query: string) => {
    searchAbortRef.current?.abort();
    const controller = new AbortController();
    searchAbortRef.current = controller;

    try {
      const location = await searchLocation(query, controller.signal);
      if (!controller.signal.aborted && location) setSelectedLocation(location);
    } catch (error: unknown) {
      if (!controller.signal.aborted) console.error(error);
    }
  }, []);

  const handleRouteImport = useCallback(async (file: File) => {
    const generation = ++routeGenerationRef.current;
    routeAbortRef.current?.abort();
    if (!file.name.toLowerCase().endsWith(".gpx")) {
      setRouteStatus("error");
      setRouteStatusMessage("Choose a .gpx route file.");
      return;
    }
    if (file.size > MAX_GPX_FILE_BYTES) {
      setRouteStatus("error");
      setRouteStatusMessage("The GPX file exceeds the 15 MiB local import limit.");
      return;
    }
    setRouteStatus("parsing");
    setRouteStatusMessage("Reading GPX route…");
    try {
      const fallbackName = file.name.replace(/\.gpx$/i, "") || "Imported route";
      const imported = parseGpxText(await file.text(), fallbackName);
      const resampled = resampleRouteGeometry(imported);
      if (generation !== routeGenerationRef.current) return;
      setRouteGeometry(resampled);
      setTerrainRoute(null);
      setRouteConditions(null);
      setRouteConditionStatus("idle");
      setFocusedRouteSampleIndex(null);
      setRouteStatus("loading-elevation");
      setRouteStatusMessage("Loading terrain elevation…");
      const controller = new AbortController();
      routeAbortRef.current = controller;
      const elevations = await sampleTerrainElevations(
        resampled.coordinates,
        controller.signal,
        (completed, total) => {
          if (generation !== routeGenerationRef.current) return;
          setRouteStatusMessage(`Loading terrain elevation · ${completed}/${total} tiles`);
        }
      );
      if (generation !== routeGenerationRef.current || controller.signal.aborted) return;
      const enriched = buildTerrainRoute(resampled, elevations);
      setTerrainRoute(enriched);
      setRouteStatus(
        enriched.elevationCoverage === "complete" ? "ready" : "partial"
      );
      setRouteStatusMessage(
        enriched.elevationCoverage === "complete"
          ? "Terrain and timing ready"
          : "Some terrain elevation is unavailable; timing is withheld."
      );
    } catch (error) {
      if (generation !== routeGenerationRef.current) return;
      setRouteStatus("error");
      setRouteStatusMessage(
        error instanceof Error ? error.message : "The route could not be prepared."
      );
    }
  }, []);

  const handleRouteClear = useCallback(() => {
    routeGenerationRef.current += 1;
    routeAbortRef.current?.abort();
    routeConditionGenerationRef.current += 1;
    routeConditionAbortRef.current?.abort();
    setRouteGeometry(null);
    setTerrainRoute(null);
    setFocusedRouteSampleIndex(null);
    setRouteConditions(null);
    setRouteConditionStatus("idle");
    setRouteConditionMode("none");
    setRouteStatus("idle");
    setRouteStatusMessage(null);
  }, []);

  const handleOverlayChange = useCallback(
    (overlay: keyof MapOverlayState, enabled: boolean) => {
      const nextSource =
        overlay === "precipitation"
          ? globalPrecipitationSource
          : overlay === "clouds"
            ? globalCloudSource
            : overlay === "windFlow"
              ? globalWindSource
              : overlay === "temperatureContours"
                ? globalTemperatureSource
            : null;
      if (enabled && nextSource && !hasInitialisedGfsTimelineRef.current) {
        const firstFutureIndex = nextSource.manifest.timesteps.findIndex(
          (step) => new Date(step.validTime).getTime() >= Date.now()
        );
        setForecastHour(firstFutureIndex >= 0 ? firstFutureIndex : 0);
        hasInitialisedGfsTimelineRef.current = true;
      }
      setMapOverlays((current) => ({
        ...current,
        [overlay]: enabled,
      }));
    },
    [
      globalCloudSource,
      globalPrecipitationSource,
      globalTemperatureSource,
      globalWindSource,
    ]
  );
  const activeRouteConditions = journeyResult.schedule ? routeConditions : null;
  const activeRouteConditionStatus = journeyResult.schedule
    ? routeConditionStatus
    : "idle";

  return (
    <main className="app-shell">
      <MapView
        selectedLocation={selectedLocation}
        basemap={basemap}
        mapOverlays={mapOverlays}
        weatherGrid={weatherGrid}
        weatherGridHistory={weatherGridHistory}
        weatherGridStatus={weatherGridStatus}
        globalPrecipitationSource={globalPrecipitationSource}
        globalCloudSource={globalCloudSource}
        globalWindSource={globalWindSource}
        globalTemperatureSource={globalTemperatureSource}
        globalWeatherStatuses={globalWeatherStatuses}
        activeGlobalValidTime={activeGlobalValidTime}
        localForecastHour={localForecastHour}
        routeGeometry={routeGeometry}
        terrainRoute={terrainRoute}
        focusedRouteSampleIndex={focusedRouteSampleIndex}
        routeConditions={activeRouteConditions}
        routeConditionMode={routeConditionMode}
        panelCollapsed={isDesktopPanelCollapsed}
        onLocationSelect={setSelectedLocation}
        onRouteSampleFocus={setFocusedRouteSampleIndex}
        onWeatherGridRequest={handleWeatherGridRequest}
      />

      <WeatherPanel
        selectedLocation={selectedLocation}
        weather={weather}
        place={place}
        basemap={basemap}
        mapOverlays={mapOverlays}
        forecastHour={activeForecastHour}
        weatherGrid={weatherGrid}
        weatherGridStatus={weatherGridStatus}
        globalPrecipitationSource={globalPrecipitationSource}
        globalCloudSource={globalCloudSource}
        globalWindSource={globalWindSource}
        globalTemperatureSource={globalTemperatureSource}
        globalWeatherStatuses={globalWeatherStatuses}
        globalWeatherCatalog={globalWeatherCatalog}
        catalogueCheck={catalogueCheck}
        journeySchedule={journeyResult.schedule}
        activeGlobalValidTime={activeGlobalValidTime}
        forecastTimes={forecastTimes}
        forecastHours={forecastHours}
        isDesktopCollapsed={isDesktopPanelCollapsed}
        satelliteAvailable={IS_SATELLITE_CONFIGURED}
        onForecastHourChange={setForecastHour}
        onBasemapChange={setBasemap}
        onOverlayChange={handleOverlayChange}
        onSearch={handleSearch}
        onDesktopCollapsedChange={setIsDesktopPanelCollapsed}
        routePanel={
          <RoutePlannerPanel
            routeGeometry={routeGeometry}
            terrainRoute={terrainRoute}
            schedule={journeyResult.schedule}
            scheduleError={journeyResult.error}
            status={routeStatus}
            statusMessage={routeStatusMessage}
            profile={journeyProfile}
            plan={journeyPlan}
            focusedIndex={focusedRouteSampleIndex}
            routeConditions={activeRouteConditions}
            routeConditionStatus={activeRouteConditionStatus}
            routeConditionMode={routeConditionMode}
            onImport={handleRouteImport}
            onClear={handleRouteClear}
            onProfileChange={setJourneyProfile}
            onPlanChange={setJourneyPlan}
            onFocusChange={setFocusedRouteSampleIndex}
            onRouteConditionModeChange={setRouteConditionMode}
          />
        }
      />
    </main>
  );
}

export default App;
