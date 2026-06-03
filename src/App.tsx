import { useEffect, useState } from "react";

import MapView from "./components/MapView";
import WeatherPanel from "./components/WeatherPanel";

import { getWeather } from "./services/weatherService";
import { getLocationName } from "./services/locationService";
import { searchLocation } from "./services/searchService";
import { getWeatherGrid } from "./services/gridWeatherService";

import type { SelectedLocation } from "./types/location";
import type { WeatherData } from "./types/weather";
import type { Place } from "./types/place";
import type { WeatherLayer } from "./types/layer";
import type { GridPoint } from "./types/gridPoint";

import "./App.css";

const WEATHER_GRID_LAYERS: WeatherLayer[] = [
  "temperature",
  "clouds",
  "precipitation",
  "pressure",
  "wind",
];

function App() {
  const [selectedLocation, setSelectedLocation] =
    useState<SelectedLocation | null>(null);

  const [debouncedLocation, setDebouncedLocation] =
    useState<SelectedLocation | null>(null);

  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [place, setPlace] = useState<Place | null>(null);

  const [selectedLayer, setSelectedLayer] =
    useState<WeatherLayer>("none");

  const [gridPoints, setGridPoints] =
    useState<GridPoint[]>([]);

  const [forecastHour, setForecastHour] = 
    useState(0);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      setDebouncedLocation(selectedLocation);
    }, 500);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [selectedLocation]);

  useEffect(() => {
    if (!debouncedLocation) return;

    getWeather(
      debouncedLocation.latitude,
      debouncedLocation.longitude
    )
      .then(setWeather)
      .catch(console.error);

    getLocationName(
      debouncedLocation.latitude,
      debouncedLocation.longitude
    )
      .then((name) => setPlace({ name }))
      .catch(console.error);

    getWeatherGrid(debouncedLocation)
      .then(setGridPoints)
      .catch(console.error);
  }, [debouncedLocation]);

  const handleSearch = async (query: string) => {
    const location = await searchLocation(query);

    if (location) {
      setSelectedLocation(location);
    }
  };

  const visibleGridPoints = WEATHER_GRID_LAYERS.includes(selectedLayer)
    ? gridPoints
    : [];

  return (
    <main className="app-shell">
      <MapView
        selectedLocation={selectedLocation}
        selectedLayer={selectedLayer}
        gridPoints={visibleGridPoints}
        onLocationSelect={setSelectedLocation}
      />

      <WeatherPanel
        selectedLocation={selectedLocation}
        weather={weather}
        place={place}
        selectedLayer={selectedLayer}
        forecastHour={forecastHour}
        onForecastHourChange={setForecastHour}
        onLayerChange={setSelectedLayer}
        onSearch={handleSearch}
      />
    </main>
  );
}

export default App;