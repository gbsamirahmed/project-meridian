import { useEffect, useState } from "react";
import type { FormEvent, ReactNode } from "react";

import ForecastPanel from "./ForecastPanel";
import LayerLegend from "./LayerLegend";
import LayerPanel from "./LayerPanel";
import TimeSlider from "./TimeSlider";
import WeatherFreshness from "./WeatherFreshness";
import { accumulationIntervalLabel } from "../services/weatherTimeLabel";

import type { Basemap, MapOverlayState } from "../types/layer";
import type { SelectedLocation } from "../types/location";
import type { Place } from "../types/place";
import type { WeatherData } from "../types/weather";
import type { JourneySchedule } from "../types/route";
import type { CatalogueCheckState } from "../services/weatherCatalogueRefresh";
import type {
  GlobalWeatherCatalog,
  GlobalWeatherStatusRegistry,
  ScalarWeatherFieldSource,
  VectorWeatherFieldSource,
} from "../types/globalWeather";
import {
  getScalarTimestepAtTime,
  getVectorTimestepAtTime,
} from "../services/globalWeatherService";

interface WeatherPanelProps {
  selectedLocation: SelectedLocation | null;
  weather: WeatherData | null;
  place: Place | null;
  basemap: Basemap;
  mapOverlays: MapOverlayState;
  forecastHour: number;
  globalPrecipitationSource: ScalarWeatherFieldSource | null;
  globalCloudSource: ScalarWeatherFieldSource | null;
  globalWindSource: VectorWeatherFieldSource | null;
  globalTemperatureSource: ScalarWeatherFieldSource | null;
  globalPressureSource: ScalarWeatherFieldSource | null;
  globalWeatherStatuses: GlobalWeatherStatusRegistry;
  globalWeatherCatalog: GlobalWeatherCatalog | null;
  catalogueCheck: CatalogueCheckState;
  journeySchedule: JourneySchedule | null;
  activeGlobalValidTime: string | null;
  forecastTimes: string[];
  forecastHours?: number[];
  isDesktopCollapsed: boolean;
  satelliteAvailable: boolean;
  onForecastHourChange: (hour: number) => void;
  onBasemapChange: (basemap: Basemap) => void;
  onOverlayChange: (
    overlay: keyof MapOverlayState,
    enabled: boolean
  ) => void;
  onSearch: (query: string) => void;
  onDesktopCollapsedChange: (collapsed: boolean) => void;
  routePanel: ReactNode;
}

export default function WeatherPanel({
  selectedLocation,
  weather,
  place,
  basemap,
  mapOverlays,
  forecastHour,
  globalPrecipitationSource,
  globalCloudSource,
  globalWindSource,
  globalTemperatureSource,
  globalPressureSource,
  globalWeatherStatuses,
  globalWeatherCatalog,
  catalogueCheck,
  journeySchedule,
  activeGlobalValidTime,
  forecastTimes,
  forecastHours,
  isDesktopCollapsed,
  satelliteAvailable,
  onForecastHourChange,
  onBasemapChange,
  onOverlayChange,
  onSearch,
  onDesktopCollapsedChange,
  routePanel,
}: WeatherPanelProps) {
  const [query, setQuery] = useState("");
  const [isPlaying, setIsPlaying] = useState(false);
  const globalPrecipitationActive =
    mapOverlays.precipitation && globalPrecipitationSource !== null;
  const globalCloudActive = mapOverlays.clouds && globalCloudSource !== null;
  const globalWindActive = mapOverlays.windFlow && globalWindSource !== null;
  const globalTemperatureActive =
    mapOverlays.temperatureContours && globalTemperatureSource !== null;
  const globalPressureActive =
    mapOverlays.pressureIsobars && globalPressureSource !== null;
  const globalPrecipitationTimestep = globalPrecipitationSource
    ? getScalarTimestepAtTime(globalPrecipitationSource, activeGlobalValidTime)
    : null;
  const globalCloudTimestep = globalCloudSource
    ? getScalarTimestepAtTime(globalCloudSource, activeGlobalValidTime)
    : null;
  const globalWindTimestep = globalWindSource
    ? getVectorTimestepAtTime(globalWindSource, activeGlobalValidTime)
    : null;
  const globalTemperatureTimestep = globalTemperatureSource
    ? getScalarTimestepAtTime(globalTemperatureSource, activeGlobalValidTime)
    : null;
  const globalPressureTimestep = globalPressureSource
    ? getScalarTimestepAtTime(globalPressureSource, activeGlobalValidTime)
    : null;
  const globalFieldsActive =
    globalPrecipitationActive ||
    globalCloudActive ||
    globalWindActive ||
    globalTemperatureActive ||
    globalPressureActive;
  const globalFieldLabel = [
    globalPrecipitationActive ? "precipitation" : null,
    globalCloudActive ? "cloud" : null,
    globalWindActive ? "wind" : null,
    globalTemperatureActive ? "temperature" : null,
    globalPressureActive ? "pressure" : null,
  ]
    .filter(Boolean)
    .join(" + ");
  const unavailableGlobalField =
    mapOverlays.clouds && !globalCloudSource
      ? "cloud cover"
      : mapOverlays.precipitation && !globalPrecipitationSource
        ? "precipitation"
        : mapOverlays.windFlow && !globalWindSource
          ? "wind"
        : mapOverlays.temperatureContours && !globalTemperatureSource
          ? "temperature"
        : mapOverlays.pressureIsobars && !globalPressureSource
          ? "pressure"
        : null;
  const activeRunTimes = Array.from(
    new Set(
      [
        globalPrecipitationActive
          ? globalPrecipitationSource?.manifest.runTime
          : null,
        globalCloudActive ? globalCloudSource?.manifest.runTime : null,
        globalWindActive ? globalWindSource?.manifest.runTime : null,
        globalTemperatureActive ? globalTemperatureSource?.manifest.runTime : null,
        globalPressureActive ? globalPressureSource?.manifest.runTime : null,
      ].filter((runTime): runTime is string => Boolean(runTime))
    )
  );
  const runLabel = activeRunTimes
    .map((runTime) => runTime.replace("T", " ").replace(":00:00Z", "Z"))
    .join(" / ");

  const handleSearchSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!query.trim()) return;

    onSearch(query.trim());
    setQuery("");
  };

  useEffect(() => {
    if (!isPlaying) return;

    const interval = setInterval(() => {
      const maximumIndex = Math.max(0, forecastTimes.length - 1);
      onForecastHourChange(forecastHour >= maximumIndex ? 0 : forecastHour + 1);
    }, 500);

    return () => clearInterval(interval);
  }, [isPlaying, forecastHour, forecastTimes.length, onForecastHourChange]);

  useEffect(() => {
    const mobileQuery = window.matchMedia("(max-width: 700px)");
    const expandForMobile = (event: MediaQueryListEvent | MediaQueryList) => {
      if (event.matches) onDesktopCollapsedChange(false);
    };

    expandForMobile(mobileQuery);
    mobileQuery.addEventListener("change", expandForMobile);
    return () => mobileQuery.removeEventListener("change", expandForMobile);
  }, [onDesktopCollapsedChange]);

  return (
    <aside
      className={`weather-panel${isDesktopCollapsed ? " weather-panel-collapsed" : ""}`}
      aria-label="Weather explorer"
    >
      <button
        type="button"
        className="panel-collapse-button"
        aria-label={
          isDesktopCollapsed ? "Expand weather panel" : "Collapse weather panel"
        }
        aria-expanded={!isDesktopCollapsed}
        onClick={() => onDesktopCollapsedChange(!isDesktopCollapsed)}
      >
        <span className={isDesktopCollapsed ? "collapsed-brand-mark" : undefined} aria-hidden="true">{isDesktopCollapsed ? "M" : "×"}</span>
      </button>

      <div className="panel-content" aria-hidden={isDesktopCollapsed}>
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

      <WeatherFreshness
        catalog={globalWeatherCatalog}
        check={catalogueCheck}
        journey={journeySchedule}
      />

      {routePanel}

      <LayerPanel
        basemap={basemap}
        mapOverlays={mapOverlays}
        satelliteAvailable={satelliteAvailable}
        onBasemapChange={onBasemapChange}
        onOverlayChange={onOverlayChange}
      />

      <section className="weather-card data-resolution-card">
        <div className="resolution-heading">
          <span
            className={`data-status data-status-${globalFieldsActive ? "ready" : "idle"}`}
            aria-hidden="true"
          />
          <strong>
            {globalFieldsActive
              ? `GFS 0.25° global ${globalFieldLabel} · +${globalPrecipitationTimestep?.forecastHour ?? globalCloudTimestep?.forecastHour ?? globalWindTimestep?.forecastHour ?? globalTemperatureTimestep?.forecastHour ?? globalPressureTimestep?.forecastHour ?? 0}h${unavailableGlobalField ? ` · ${unavailableGlobalField} unavailable` : ""}`
              : (mapOverlays.precipitation || mapOverlays.clouds || mapOverlays.windFlow || mapOverlays.temperatureContours || mapOverlays.pressureIsobars) &&
                  (globalWeatherStatuses.precipitation === "loading" ||
                    globalWeatherStatuses.cloud_cover === "loading" ||
                    globalWeatherStatuses.wind_10m === "loading" ||
                    globalWeatherStatuses.temperature_2m === "loading" ||
                    globalWeatherStatuses.pressure_msl === "loading")
                ? "Loading global weather metadata"
                : mapOverlays.precipitation && globalWeatherStatuses.precipitation !== "ready"
                  ? "Global precipitation unavailable"
                : mapOverlays.clouds && globalWeatherStatuses.cloud_cover !== "ready"
                  ? "Global cloud cover unavailable"
                : mapOverlays.windFlow && globalWeatherStatuses.wind_10m !== "ready"
                  ? "Global wind unavailable"
                : mapOverlays.temperatureContours && globalWeatherStatuses.temperature_2m !== "ready"
                  ? "Global temperature unavailable"
                : mapOverlays.pressureIsobars && globalWeatherStatuses.pressure_msl !== "ready"
                  ? "Global pressure unavailable"
                  : "No global weather overlay selected"}
          </strong>
        </div>
        <p>
          {globalFieldsActive
            ? `NOAA GFS run ${runLabel}; valid ${activeGlobalValidTime?.replace("T", " ").replace("Z", " UTC")}. ${unavailableGlobalField ? `${unavailableGlobalField[0].toUpperCase()}${unavailableGlobalField.slice(1)} is unavailable with no regional map fallback. ` : "Cloud, 10 m wind, 2 m temperature and mean sea-level pressure are instantaneous; precipitation is an honest interval total."}`
            : (mapOverlays.precipitation && globalWeatherStatuses.precipitation !== "ready") ||
                (mapOverlays.clouds && globalWeatherStatuses.cloud_cover !== "ready") ||
                (mapOverlays.windFlow && globalWeatherStatuses.wind_10m !== "ready") ||
                (mapOverlays.temperatureContours && globalWeatherStatuses.temperature_2m !== "ready") ||
                (mapOverlays.pressureIsobars && globalWeatherStatuses.pressure_msl !== "ready")
              ? "Run the documented local GFS update to publish the unavailable field. Meridian does not silently substitute regional map data."
              : "Map weather fields are loaded from the active global GFS catalogue."}
        </p>
      </section>

      <TimeSlider
        forecastHour={forecastHour}
        forecastTimes={forecastTimes}
        forecastHours={forecastHours}
        sourceLabel={globalFieldsActive
          ? `GFS valid-time steps${globalPrecipitationActive && globalPrecipitationTimestep
            ? ` · Precipitation: ${accumulationIntervalLabel(globalPrecipitationTimestep)}` : ""}`
          : undefined}
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
        mapOverlays={mapOverlays}
        globalPrecipitationActive={globalPrecipitationActive}
        precipitationAccumulationHours={globalPrecipitationTimestep?.accumulationHours}
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
      </div>
    </aside>
  );
}
