import { useEffect, useState } from "react";
import MapView from "./components/MapView";
import WeatherPanel from "./components/WeatherPanel";
import { getWeather } from "./services/weatherService";
import { getLocationName } from "./services/locationService";
import { searchLocation } from "./services/searchService";

import type { SelectedLocation } from "./types/location";
import type { WeatherData } from "./types/weather";
import type { Place } from "./types/place";

import "./App.css";

function App() {
  const [selectedLocation, setSelectedLocation] =
    useState<SelectedLocation | null>(null);

  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [place, setPlace] = useState<Place | null>(null);

  useEffect(() => {
    if (!selectedLocation) return;

    getWeather(selectedLocation.latitude, selectedLocation.longitude)
      .then(setWeather)
      .catch(console.error);

    getLocationName(selectedLocation.latitude, selectedLocation.longitude)
      .then((name) => setPlace({ name }))
      .catch(console.error);
  }, [selectedLocation]);

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
        onLocationSelect={setSelectedLocation}
      />

      <WeatherPanel
        selectedLocation={selectedLocation}
        weather={weather}
        place={place}
        onSearch={handleSearch}
      />
    </main>
  );
}

export default App;