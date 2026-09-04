import LayerLegend from "./LayerLegend";
import WeatherFreshness from "./WeatherFreshness";
import { accumulationIntervalLabel } from "../services/weatherTimeLabel";
import { getScalarTimestepAtTime } from "../services/globalWeatherService";
import { MAP_OVERLAY_TOOLS } from "../services/desktopControlOptions";
import type { CatalogueCheckState } from "../services/weatherCatalogueRefresh";
import type { GlobalWeatherCatalog, GlobalWeatherStatusRegistry, ScalarWeatherFieldSource, VectorWeatherFieldSource } from "../types/globalWeather";
import type { Basemap, MapOverlayState } from "../types/layer";
import type { JourneySchedule } from "../types/route";
import type { WeatherGridStatus } from "../types/weatherGrid";

interface MapControlsProps {
  basemap: Basemap;
  mapOverlays: MapOverlayState;
  satelliteAvailable: boolean;
  forecastHour: number;
  forecastTimes: string[];
  forecastHours?: number[];
  activeGlobalValidTime: string | null;
  globalPrecipitationSource: ScalarWeatherFieldSource | null;
  globalCloudSource: ScalarWeatherFieldSource | null;
  globalWindSource: VectorWeatherFieldSource | null;
  globalTemperatureSource: ScalarWeatherFieldSource | null;
  globalWeatherStatuses: GlobalWeatherStatusRegistry;
  globalWeatherCatalog: GlobalWeatherCatalog | null;
  catalogueCheck: CatalogueCheckState;
  journeySchedule: JourneySchedule | null;
  weatherGridStatus: WeatherGridStatus;
  onBasemapChange: (basemap: Basemap) => void;
  onOverlayChange: (overlay: keyof MapOverlayState, enabled: boolean) => void;
  onForecastHourChange: (hour: number) => void;
  isPlaying: boolean;
  onPlayingChange: (playing: boolean) => void;
  onClose: () => void;
}

function formatForecastTime(time?: string): string {
  if (!time) return "No forecast";
  const normalized = /(?:Z|[+-]\d{2}:?\d{2})$/.test(time) ? time : `${time}Z`;
  return new Intl.DateTimeFormat("en-GB", {
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit",
    timeZoneName: "short",
  }).format(new Date(normalized));
}

export default function MapControls({ basemap, mapOverlays, satelliteAvailable, forecastHour, forecastTimes, forecastHours, activeGlobalValidTime, globalPrecipitationSource, globalCloudSource, globalWindSource, globalTemperatureSource, globalWeatherStatuses, globalWeatherCatalog, catalogueCheck, journeySchedule, weatherGridStatus, onBasemapChange, onOverlayChange, onForecastHourChange, isPlaying, onPlayingChange, onClose }: MapControlsProps) {
  const precipActive = mapOverlays.precipitation && globalPrecipitationSource !== null;
  const cloudActive = mapOverlays.clouds && globalCloudSource !== null;
  const windActive = mapOverlays.windFlow && globalWindSource !== null;
  const temperatureActive = mapOverlays.temperatureContours && globalTemperatureSource !== null;
  const hasOverlay = Object.values(mapOverlays).some(Boolean);
  const globalActive = precipActive || cloudActive || windActive || temperatureActive;
  const precipitationStep = globalPrecipitationSource ? getScalarTimestepAtTime(globalPrecipitationSource, activeGlobalValidTime) : null;
  const globalLoading = Object.values(globalWeatherStatuses).some((status) => status === "loading");
  const maximumIndex = Math.max(0, forecastTimes.length - 1);
  const displayedForecastHour = forecastHours?.[forecastHour] ?? forecastHour;
  const forecastLabel = formatForecastTime(forecastTimes[forecastHour]);

  return (
    <div className="map-controls-native" aria-label="Map controls">
      <aside className="map-tool-strip desktop-surface">
        <button type="button" className="map-tool-close" aria-label="Hide map controls" onClick={onClose}>×</button>
        <button type="button" className={`map-tool-button${basemap === "terrain" ? " active" : ""}`} aria-pressed={basemap === "terrain"} title="Terrain basemap" onClick={() => onBasemapChange("terrain")}><span aria-hidden="true">◒</span><small>Terrain</small></button>
        <button type="button" className={`map-tool-button${basemap === "satellite" ? " active" : ""}`} aria-pressed={basemap === "satellite"} disabled={!satelliteAvailable} title={satelliteAvailable ? "Satellite basemap" : "Satellite requires a configured MapTiler key"} onClick={() => onBasemapChange("satellite")}><span aria-hidden="true">◉</span><small>Satellite</small></button>
        <div className="map-tool-divider" />
        {MAP_OVERLAY_TOOLS.map((tool) => (
          <button key={tool.key} type="button" className={`map-tool-button${mapOverlays[tool.key] ? " active" : ""}`} aria-pressed={mapOverlays[tool.key]} title={tool.label} onClick={() => onOverlayChange(tool.key, !mapOverlays[tool.key])}>
            <span aria-hidden="true">{tool.key === "precipitation" ? "≋" : tool.key === "windFlow" ? "↝" : tool.key === "clouds" ? "☁" : tool.key === "temperatureContours" ? "°" : tool.key === "pressureIsobars" ? "P" : "△"}</span>
            <small>{tool.shortLabel}</small>
          </button>
        ))}
      </aside>

      <section className="forecast-float desktop-surface" aria-label="Forecast timeline">
        <button type="button" className="forecast-play-button" aria-label={isPlaying ? "Pause forecast" : "Play forecast"} aria-pressed={isPlaying} onClick={() => onPlayingChange(!isPlaying)}>{isPlaying ? "Ⅱ" : "▶"}</button>
        <div className="forecast-float-main">
          <div className="forecast-float-heading"><strong>{forecastLabel}</strong><span>+{displayedForecastHour}h</span></div>
          <input className="time-slider" type="range" aria-label="Forecast hour" min="0" max={maximumIndex} step="1" value={forecastHour} onChange={(event) => onForecastHourChange(Number(event.target.value))} />
        </div>
        <details className="map-data-details">
          <summary>Data</summary>
          <div className="map-data-popover desktop-surface">
            <WeatherFreshness catalog={globalWeatherCatalog} check={catalogueCheck} journey={journeySchedule} />
            <p className="map-data-status">{globalActive ? `GFS +${displayedForecastHour}h${precipActive && precipitationStep ? ` · Rain ${accumulationIntervalLabel(precipitationStep)}` : ""}` : globalLoading ? "Loading GFS metadata" : "No global weather overlay selected"}</p>
            {hasOverlay && <LayerLegend mapOverlays={mapOverlays} globalPrecipitationActive={precipActive} precipitationAccumulationHours={precipitationStep?.accumulationHours} />}
            {mapOverlays.pressureIsobars && <p className="pressure-note">Regional pressure uses a 9 × 9 Open-Meteo sample grid. This label applies only to pressure.</p>}
            {mapOverlays.pressureIsobars && weatherGridStatus === "error" && <p className="status-message error">Regional pressure is unavailable.</p>}
          </div>
        </details>
      </section>
    </div>
  );
}
