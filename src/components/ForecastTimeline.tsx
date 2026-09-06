import LayerLegend from "./LayerLegend";
import WeatherFreshness from "./WeatherFreshness";
import { accumulationIntervalLabel } from "../services/weatherTimeLabel";
import { getScalarTimestepAtTime } from "../services/globalWeatherService";
import type { CatalogueCheckState } from "../services/weatherCatalogueRefresh";
import type { GlobalWeatherCatalog, GlobalWeatherStatusRegistry, ScalarWeatherFieldSource, VectorWeatherFieldSource } from "../types/globalWeather";
import type { MapOverlayState } from "../types/layer";
import type { JourneySchedule } from "../types/route";
import type { WeatherGridStatus } from "../types/weatherGrid";

interface ForecastTimelineProps {
  mapOverlays: MapOverlayState;
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
  onForecastHourChange: (hour: number) => void;
  isPlaying: boolean;
  onPlayingChange: (playing: boolean) => void;
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

export default function ForecastTimeline({ mapOverlays, forecastHour, forecastTimes, forecastHours, activeGlobalValidTime, globalPrecipitationSource, globalCloudSource, globalWindSource, globalTemperatureSource, globalWeatherStatuses, globalWeatherCatalog, catalogueCheck, journeySchedule, weatherGridStatus, onForecastHourChange, isPlaying, onPlayingChange }: ForecastTimelineProps) {
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

  return <section className="location-timeline workspace-card" aria-label="Forecast timeline">
    <div className="location-timeline-heading">
      <div><p className="section-kicker">Forecast time</p><strong>{forecastLabel}</strong></div>
      <span>+{displayedForecastHour}h</span>
    </div>
    <div className="location-timeline-controls">
      <button type="button" className="forecast-play-button" aria-label={isPlaying ? "Pause forecast" : "Play forecast"} aria-pressed={isPlaying} onClick={() => onPlayingChange(!isPlaying)}>{isPlaying ? "Ⅱ" : "▶"}</button>
      <input className="time-slider" type="range" aria-label="Forecast hour" min="0" max={maximumIndex} step="1" value={forecastHour} onChange={(event) => onForecastHourChange(Number(event.target.value))} />
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
    </div>
  </section>;
}