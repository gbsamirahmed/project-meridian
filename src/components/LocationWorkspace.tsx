import { useState, type FormEvent } from "react";
import ForecastPanel from "./ForecastPanel";
import type { SelectedLocation } from "../types/location";
import type { Place } from "../types/place";
import type { WeatherData } from "../types/weather";

interface LocationWorkspaceProps {
  selectedLocation: SelectedLocation | null;
  weather: WeatherData | null;
  place: Place | null;
  onSearch: (query: string) => void;
}

export default function LocationWorkspace({
  selectedLocation,
  weather,
  place,
  onSearch,
}: LocationWorkspaceProps) {
  const [query, setQuery] = useState("");
  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!query.trim()) return;
    onSearch(query.trim());
    setQuery("");
  };

  return (
    <div className="location-workspace">
      <form className="search-field" onSubmit={handleSubmit}>
        <input
          className="search-input"
          type="search"
          aria-label="Search location"
          placeholder="Find a mountain or place"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <button type="submit" aria-label="Search">Go</button>
      </form>

      <section className="workspace-card location-summary-card">
        <p className="section-kicker">Selected location</p>
        {selectedLocation ? (
          <div className="location-content">
            <h2 title={place?.name}>{place?.name ?? "Finding place..."}</h2>
            <p className="coordinates">
              {selectedLocation.latitude.toFixed(4)}, {selectedLocation.longitude.toFixed(4)}
            </p>
          </div>
        ) : (
          <div className="empty-state">
            <span className="empty-state-marker" aria-hidden="true" />
            <p>Search or click the map to select a location.</p>
          </div>
        )}
      </section>

      <section className="workspace-card current-weather-card">
        <div className="card-heading">
          <div>
            <p className="section-kicker">At this location</p>
            <h2>Current conditions</h2>
          </div>
          {weather && <span className="live-badge"><span /> Live</span>}
        </div>
        {weather ? (
          <div className="current-weather-content">
            <div className="temperature-reading">
              <strong>{Math.round(weather.temperature)}°</strong>
              <span>Air temperature</span>
            </div>
            <div className="weather-metrics">
              <div><span>Wind</span><strong>{weather.windSpeed} km/h</strong></div>
              <div><span>Gusts</span><strong>{weather.windGusts} km/h</strong></div>
              <div><span>Rain</span><strong>{weather.precipitation} mm</strong></div>
              <div><span>Cloud</span><strong>{weather.cloudCover}%</strong></div>
              <div><span>Visibility</span><strong>{weather.visibility.toFixed(1)} km</strong></div>
              <div><span>Pressure</span><strong>{Math.round(weather.pressure)} hPa</strong></div>
              <div><span>Humidity</span><strong>{weather.humidity}%</strong></div>
              <div><span>Dew point</span><strong>{weather.dewPoint}°</strong></div>
            </div>
          </div>
        ) : (
          <p className="muted-copy">Select a location to load live weather and forecast data.</p>
        )}
      </section>

      {weather && <ForecastPanel forecast={weather.forecast} />}
    </div>
  );
}
