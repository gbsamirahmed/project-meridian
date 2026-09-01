import { useCallback, useEffect, useRef, useState } from "react";

import MapView from "./components/MapView";
import WeatherPanel from "./components/WeatherPanel";

import { getWeather } from "./services/weatherService";
import { getLocationName } from "./services/locationService";
import { searchLocation } from "./services/searchService";
import {
  intersectScalarValidTimes,
  loadGlobalWeatherSources,
} from "./services/globalWeatherService";
import { IS_SATELLITE_CONFIGURED } from "./config/satelliteProvider";
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
  GlobalWeatherSourceRegistry,
  GlobalWeatherStatusRegistry,
  GlobalWeatherFieldSource,
} from "./types/globalWeather";
import type {
  WeatherGrid,
  WeatherGridRequest,
  WeatherGridStatus,
} from "./types/weatherGrid";

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
  const [globalWeatherSources, setGlobalWeatherSources] =
    useState<GlobalWeatherSourceRegistry>({});
  const [globalWeatherStatuses, setGlobalWeatherStatuses] =
    useState<GlobalWeatherStatusRegistry>({
      precipitation: "loading",
      cloud_cover: "loading",
      wind_10m: "loading",
      temperature_2m: "loading",
    });
  const [isDesktopPanelCollapsed, setIsDesktopPanelCollapsed] =
    useState(false);

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
  const runWeatherGridRequestRef = useRef<
    (request: WeatherGridRequest) => void
  >(() => undefined);

  useEffect(() => {
    let isCurrent = true;
    loadGlobalWeatherSources()
      .then((result) => {
        if (!isCurrent) return;
        setGlobalWeatherSources(result.sources);
        setGlobalWeatherStatuses(result.statuses);
      })
      .catch((error: unknown) => {
        if (!isCurrent) return;
        void error;
        setGlobalWeatherStatuses({
          precipitation: "unavailable",
          cloud_cover: "unavailable",
          wind_10m: "unavailable",
          temperature_2m: "unavailable",
        });
      });

    return () => {
      isCurrent = false;
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
      if (weatherGridRetryTimerRef.current !== null) {
        window.clearTimeout(weatherGridRetryTimerRef.current);
      }
    };
  }, []);

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
        panelCollapsed={isDesktopPanelCollapsed}
        onLocationSelect={setSelectedLocation}
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
      />
    </main>
  );
}

export default App;
