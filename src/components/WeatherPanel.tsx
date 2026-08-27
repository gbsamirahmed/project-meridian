import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import ForecastPanel from "./ForecastPanel";
import LayerLegend from "./LayerLegend";
import LayerPanel from "./LayerPanel";
import TimeSlider from "./TimeSlider";

import type { PrimaryView, WeatherOverlayState } from "../types/layer";
import type { SelectedLocation } from "../types/location";
import type { Place } from "../types/place";
import type { WeatherData } from "../types/weather";
import type { WeatherGrid, WeatherGridStatus } from "../types/weatherGrid";

interface WeatherPanelProps {
  selectedLocation: SelectedLocation | null;
  weather: WeatherData | null;
  place: Place | null;
  primaryView: PrimaryView;
  weatherOverlays: WeatherOverlayState;
  forecastHour: number;
  weatherGrid: WeatherGrid | null;
  weatherGridStatus: WeatherGridStatus;
  onForecastHourChange: (hour: number) => void;
  onPrimaryViewChange: (view: PrimaryView) => void;
  onOverlayChange: (
    overlay: keyof WeatherOverlayState,
    enabled: boolean
  ) => void;
  onSearch: (query: string) => void;
}

export default function WeatherPanel({
  selectedLocation,
  weather,
  place,
  primaryView,
  weatherOverlays,
  forecastHour,
  weatherGrid,
  weatherGridStatus,
  onForecastHourChange,
  onPrimaryViewChange,
  onOverlayChange,
  onSearch,
}: WeatherPanelProps) {
  const [query, setQuery] = useState("");
  const [isPlaying, setIsPlaying] = useState(false);

  const handleSearchSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!query.trim()) return;

    onSearch(query.trim());
    setQuery("");
  };

  useEffect(() => {
    if (!isPlaying) return;

    const interval = setInterval(() => {
      onForecastHourChange(forecastHour >= 24 ? 0 : forecastHour + 1);
    }, 500);

    return () => clearInterval(interval);
  }, [isPlaying, forecastHour, onForecastHourChange]);

  return (
    <aside className="weather-panel" aria-label="Weather explorer">
      <header className="panel-header">
        <div className="brand-mark" aria-hidden="true">
          <span />
          <span />
        </div>

        <div>
          <p className="panel-kicker">Terrain weather</p>
          <h1>Meridian</h1>
        </div>
      </header>

      <p className="panel-intro">Read the forecast in the landscape.</p>

      <form className="search-field" onSubmit={handleSearchSubmit}>
        <input
          className="search-input"
          type="search"
          aria-label="Search location"
          placeholder="Find a mountain or place"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />

        <button type="submit" aria-label="Search">
          Go
        </button>
      </form>

      <LayerPanel
        primaryView={primaryView}
        weatherOverlays={weatherOverlays}
        onPrimaryViewChange={onPrimaryViewChange}
        onOverlayChange={onOverlayChange}
      />

      <section className="weather-card data-resolution-card">
        <div className="resolution-heading">
          <span
            className={`data-status data-status-${weatherGridStatus}`}
            aria-hidden="true"
          />
          <strong>
            {weatherGridStatus === "loading"
              ? "Sampling visible area"
              : weatherGridStatus === "error"
                ? "Forecast field unavailable"
                : weatherGrid
                  ? `${weatherGrid.rows} × ${weatherGrid.columns} model samples`
                  : "Viewport forecast field"}
          </strong>
        </div>
        <p>
          Views, contours and arrows interpolate the same coarse model field;
          denser marks do not mean finer forecast resolution.
        </p>
      </section>

      <TimeSlider
        forecastHour={forecastHour}
        forecastTimes={weather?.forecastTimes ?? weatherGrid?.times}
        onForecastHourChange={onForecastHourChange}
      />

      <div className="animation-controls">
        <button
          className="play-button"
          onClick={() => setIsPlaying(!isPlaying)}
        >
          <span aria-hidden="true">{isPlaying ? "II" : ">"}</span>
          {isPlaying ? "Pause" : "Play forecast"}
        </button>
      </div>

      <LayerLegend
        primaryView={primaryView}
        weatherOverlays={weatherOverlays}
      />

      <section className="weather-card location-card">
        <p className="section-kicker">Selected location</p>

        {selectedLocation ? (
          <div className="location-content">
            <h2 title={place?.name}>{place?.name ?? "Finding place..."}</h2>
            <p className="coordinates">
              {selectedLocation.latitude.toFixed(4)}, {" "}
              {selectedLocation.longitude.toFixed(4)}
            </p>
          </div>
        ) : (
          <div className="empty-state">
            <span className="empty-state-marker" aria-hidden="true" />
            <p>Search or click the map to inspect conditions.</p>
          </div>
        )}
      </section>

      <section className="weather-card current-weather-card">
        <div className="card-heading">
          <div>
            <p className="section-kicker">At this location</p>
            <h2>Current conditions</h2>
          </div>

          {weather && (
            <span className="live-badge">
              <span /> Live
            </span>
          )}
        </div>

        {weather ? (
          <div className="current-weather-content">
            <div className="temperature-reading">
              <strong>{Math.round(weather.temperature)}°</strong>
              <span>Air temperature</span>
            </div>

            <div className="weather-metrics">
              <div>
                <span>Wind</span>
                <strong>{weather.windSpeed} km/h</strong>
              </div>
              <div>
                <span>Gusts</span>
                <strong>{weather.windGusts} km/h</strong>
              </div>
              <div>
                <span>Rain</span>
                <strong>{weather.precipitation} mm</strong>
              </div>
              <div>
                <span>Cloud</span>
                <strong>{weather.cloudCover}%</strong>
              </div>
              <div>
                <span>Visibility</span>
                <strong>{weather.visibility.toFixed(1)} km</strong>
              </div>
              <div>
                <span>Pressure</span>
                <strong>{Math.round(weather.pressure)} hPa</strong>
              </div>
              <div>
                <span>Humidity</span>
                <strong>{weather.humidity}%</strong>
              </div>
              <div>
                <span>Dew point</span>
                <strong>{weather.dewPoint}°</strong>
              </div>
            </div>
          </div>
        ) : (
          <p className="muted-copy">
            Select a location to load live weather and forecast data.
          </p>
        )}
      </section>

      {weather && <ForecastPanel forecast={weather.forecast} />}
    </aside>
  );
}
