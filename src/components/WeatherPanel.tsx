import { useState } from "react";

import type { SelectedLocation } from "../types/location";
import type { WeatherData } from "../types/weather";
import type { Place } from "../types/place";

interface WeatherPanelProps {
  selectedLocation: SelectedLocation | null;
  weather: WeatherData | null;
  place: Place | null;
  onSearch: (query: string) => void;
}

export default function WeatherPanel({
  selectedLocation,
  weather,
  place,
  onSearch,
}: WeatherPanelProps) {
  const [query, setQuery] = useState("");

  return (
    <aside className="weather-panel">
      <h1>Meridian</h1>

      <input
        className="search-input"
        type="text"
        placeholder="Search location..."
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        onKeyDown={(event) => {
            if (event.key === "Enter" && query.trim()) {
                onSearch(query);
                setQuery("");
            }
        }}
      />

      <div className="weather-card">
        <h2>Selected location</h2>

        {selectedLocation ? (
          <>
            <p>{place?.name ?? "Loading..."}</p>

            <p>
              {selectedLocation.latitude.toFixed(4)},{" "}
              {selectedLocation.longitude.toFixed(4)}
            </p>
          </>
        ) : (
          <p>Click anywhere on the map.</p>
        )}
      </div>

      <div className="weather-card">
        <h2>Current weather</h2>

        {weather ? (
          <>
            <p>Temperature: {weather.temperature} °C</p>
            <p>Wind: {weather.windSpeed} km/h</p>
            <p>Cloud cover: {weather.cloudCover} %</p>
          </>
        ) : (
          <p>Select a location.</p>
        )}
      </div>
    </aside>
  );
}