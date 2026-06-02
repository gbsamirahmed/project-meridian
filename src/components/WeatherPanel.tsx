import { useState } from "react";

import ForecastPanel from "./ForecastPanel";
import LayerPanel from "./LayerPanel";

import type { SelectedLocation } from "../types/location";
import type { WeatherData } from "../types/weather";
import type { Place } from "../types/place";
import type { WeatherLayer } from "../types/layer";

interface WeatherPanelProps {
  selectedLocation: SelectedLocation | null;
  weather: WeatherData | null;
  place: Place | null;
  selectedLayer: WeatherLayer;
  onLayerChange: (layer: WeatherLayer) => void;
  onSearch: (query: string) => void;
}

export default function WeatherPanel({
  selectedLocation,
  weather,
  place,
  selectedLayer,
  onLayerChange,
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

      <LayerPanel
        selectedLayer={selectedLayer}
        onLayerChange={onLayerChange}
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
            <p>Humidity: {weather.humidity} %</p>
            <p>Pressure: {weather.pressure} hPa</p>
            <p>Wind: {weather.windSpeed} km/h</p>
            <p>Gusts: {weather.windGusts} km/h</p>
            <p>Cloud cover: {weather.cloudCover} %</p>
            <p>Precipitation: {weather.precipitation} mm</p>
          </>
        ) : (
          <p>Select a location.</p>
        )}
      </div>

      {weather && <ForecastPanel forecast={weather.forecast} />}
    </aside>
  );
}