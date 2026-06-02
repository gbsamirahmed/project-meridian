import { useEffect, useState } from "react";

import MapView from "./components/MapView";
import WeatherPanel from "./components/WeatherPanel";

import { getWeather } from "./services/weatherService";
import { getLocationName } from "./services/locationService";
import { searchLocation } from "./services/searchService";
import { getTemperatureGrid } from "./services/gridWeatherService";

import type { SelectedLocation } from "./types/location";
import type { WeatherData } from "./types/weather";
import type { Place } from "./types/place";
import type { WeatherLayer } from "./types/layer";
import type { GridPoint } from "./types/gridPoint";

import "./App.css";

function App() {
  const [selectedLocation, setSelectedLocation] =
    useState<SelectedLocation | null>(null);

  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [place, setPlace] = useState<Place | null>(null);

  const [selectedLayer, setSelectedLayer] =
    useState<WeatherLayer>("none");

  const [gridPoints, setGridPoints] =
    useState<GridPoint[]>([]);

  useEffect(() => {
    if (!selectedLocation) return;

    getWeather(selectedLocation.latitude, selectedLocation.longitude)
      .then(setWeather)
      .catch(console.error);

    getLocationName(selectedLocation.latitude, selectedLocation.longitude)
      .then((name) => setPlace({ name }))
      .catch(console.error);

    if (selectedLayer === "temperature") {
      getTemperatureGrid(selectedLocation)
        .then(setGridPoints)
        .catch(console.error);
    } else {
      setGridPoints([]);
    }
  }, [selectedLocation, selectedLayer]);

  const handleSearch = async (query: string) => {
    const location = await searchLocation(query);

    if (location) {
      setSelectedLocation(location);
    }
  };

  return (
    <main className="app-shell">
      <MapView
        selectedLocation={selectedLocation}
        selectedLayer={selectedLayer}
        gridPoints={gridPoints}
        onLocationSelect={setSelectedLocation}
      />

      <WeatherPanel
        selectedLocation={selectedLocation}
        weather={weather}
        place={place}
        selectedLayer={selectedLayer}
        onLayerChange={setSelectedLayer}
        onSearch={handleSearch}
      />
    </main>
  );
}

export default App;