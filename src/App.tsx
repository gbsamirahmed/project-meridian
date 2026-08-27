import { useCallback, useEffect, useRef, useState } from "react";

import MapView from "./components/MapView";
import WeatherPanel from "./components/WeatherPanel";

import { getWeather } from "./services/weatherService";
import { getLocationName } from "./services/locationService";
import { searchLocation } from "./services/searchService";
import { getWeatherGrid } from "./services/gridWeatherService";

import type { SelectedLocation } from "./types/location";
import type { WeatherData } from "./types/weather";
import type { Place } from "./types/place";
import type { PrimaryView, WeatherOverlayState } from "./types/layer";
import type {
  WeatherGrid,
  WeatherGridRequest,
  WeatherGridStatus,
} from "./types/weatherGrid";

import "./App.css";

function App() {
  const [selectedLocation, setSelectedLocation] =
    useState<SelectedLocation | null>(null);
  const [debouncedLocation, setDebouncedLocation] =
    useState<SelectedLocation | null>(null);
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [place, setPlace] = useState<Place | null>(null);
  const [primaryView, setPrimaryView] =
    useState<PrimaryView>("terrain");
  const [weatherOverlays, setWeatherOverlays] =
    useState<WeatherOverlayState>({
      temperatureContours: false,
      pressureIsobars: false,
      windFlow: false,
    });
  const [weatherGrid, setWeatherGrid] =
    useState<WeatherGrid | null>(null);
  const [weatherGridStatus, setWeatherGridStatus] =
    useState<WeatherGridStatus>("idle");
  const [forecastHour, setForecastHour] = useState(0);

  const weatherGridAbortRef = useRef<AbortController | null>(null);
  const weatherGridRequestIdRef = useRef(0);
  const activeWeatherRequestKeyRef = useRef<string | null>(null);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      setDebouncedLocation(selectedLocation);
    }, 500);

    return () => window.clearTimeout(timeoutId);
  }, [selectedLocation]);

  useEffect(() => {
    if (!debouncedLocation) return;

    let isCurrent = true;

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
      debouncedLocation.longitude
    )
      .then((name) => {
        if (isCurrent) setPlace({ name });
      })
      .catch((error: unknown) => {
        if (isCurrent) console.error(error);
      });

    return () => {
      isCurrent = false;
    };
  }, [debouncedLocation]);

  useEffect(() => {
    return () => weatherGridAbortRef.current?.abort();
  }, []);

  const handleWeatherGridRequest = useCallback(
    (request: WeatherGridRequest) => {
      const requestKey = JSON.stringify(request);

      if (activeWeatherRequestKeyRef.current === requestKey) return;

      weatherGridAbortRef.current?.abort();

      const controller = new AbortController();
      const requestId = weatherGridRequestIdRef.current + 1;

      weatherGridAbortRef.current = controller;
      weatherGridRequestIdRef.current = requestId;
      activeWeatherRequestKeyRef.current = requestKey;
      setWeatherGridStatus("loading");

      getWeatherGrid(request, controller.signal)
        .then((nextGrid) => {
          if (weatherGridRequestIdRef.current !== requestId) return;

          setWeatherGrid(nextGrid);
          setWeatherGridStatus("ready");
        })
        .catch((error: unknown) => {
          if (controller.signal.aborted) return;
          if (weatherGridRequestIdRef.current !== requestId) return;

          setWeatherGridStatus("error");
          console.error(error);
        })
        .finally(() => {
          if (weatherGridRequestIdRef.current === requestId) {
            activeWeatherRequestKeyRef.current = null;
          }
        });
    },
    []
  );

  const handleSearch = async (query: string) => {
    const location = await searchLocation(query);

    if (location) setSelectedLocation(location);
  };

  const handleOverlayChange = useCallback(
    (overlay: keyof WeatherOverlayState, enabled: boolean) => {
      setWeatherOverlays((current) => ({
        ...current,
        [overlay]: enabled,
      }));
    },
    []
  );

  return (
    <main className="app-shell">
      <MapView
        selectedLocation={selectedLocation}
        primaryView={primaryView}
        weatherOverlays={weatherOverlays}
        weatherGrid={weatherGrid}
        weatherGridStatus={weatherGridStatus}
        forecastHour={forecastHour}
        onLocationSelect={setSelectedLocation}
        onWeatherGridRequest={handleWeatherGridRequest}
      />

      <WeatherPanel
        selectedLocation={selectedLocation}
        weather={weather}
        place={place}
        primaryView={primaryView}
        weatherOverlays={weatherOverlays}
        forecastHour={forecastHour}
        weatherGrid={weatherGrid}
        weatherGridStatus={weatherGridStatus}
        onForecastHourChange={setForecastHour}
        onPrimaryViewChange={setPrimaryView}
        onOverlayChange={handleOverlayChange}
        onSearch={handleSearch}
      />
    </main>
  );
}

export default App;
