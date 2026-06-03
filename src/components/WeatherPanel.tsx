import { useState } from "react";

import ForecastPanel from "./ForecastPanel";
import LayerPanel from "./LayerPanel";
import TimeSlider from "./TimeSlider";

import type { SelectedLocation } from "../types/location";
import type { WeatherData } from "../types/weather";
import type { Place } from "../types/place";
import type { WeatherLayer } from "../types/layer";

interface WeatherPanelProps {
  selectedLocation: SelectedLocation | null;
  weather: WeatherData | null;
  place: Place | null;
  selectedLayer: WeatherLayer;
  forecastHour: number;
  onForecastHourChange: (hour: number) => void;
  onLayerChange: (layer: WeatherLayer) => void;
  onSearch: (query: string) => void;
}

export default function WeatherPanel({
  selectedLocation,
  weather,
  place,
  selectedLayer,
  forecastHour,
  onForecastHourChange,
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

      <TimeSlider
        forecastHour={forecastHour}
        onForecastHourChange={onForecastHourChange}
      />

      <div className="weather-card">
        <h2>Selected Location</h2>

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
        <h2>Current Weather</h2>

        {weather ? (
          <>
            <p>Temperature: {weather.temperature} °C</p>
            <p>Humidity: {weather.humidity} %</p>
            <p>Dew Point: {weather.dewPoint} °C</p>
            <p>Pressure: {weather.pressure} hPa</p>
            <p>Wind: {weather.windSpeed} km/h</p>
            <p>Gusts: {weather.windGusts} km/h</p>
            <p>Cloud Cover: {weather.cloudCover} %</p>
            <p>Precipitation: {weather.precipitation} mm</p>
            <p>Visibility: {weather.visibility.toFixed(1)} km</p>
          </>
        ) : (
          <p>Select a location.</p>
        )}
      </div>

      {weather && <ForecastPanel forecast={weather.forecast} />}
    </aside>
  );
}