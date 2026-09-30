import LayerLegend from "./LayerLegend";
import WeatherFreshness from "../../weather/components/WeatherFreshness";
import { accumulationIntervalLabel } from "../../weather/presentation/weatherTimeLabel";
import { getScalarTimestepAtTime } from "../../weather/data/globalWeatherService";
import type { CatalogueCheckState } from "../../weather/data/weatherCatalogueRefresh";
import type { GlobalWeatherCatalog, GlobalWeatherStatusRegistry, ScalarWeatherFieldSource, VectorWeatherFieldSource } from "../../weather/types/globalWeather";
import type { MapOverlayState } from "../state/mapOverlayState";
import type { ForecastCoverageWindow } from "../../weather/types/forecastCoverage";

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
  globalPressureSource: ScalarWeatherFieldSource | null;
  globalWeatherStatuses: GlobalWeatherStatusRegistry;
  globalWeatherCatalog: GlobalWeatherCatalog | null;
  catalogueCheck: CatalogueCheckState;
  weatherCoverage: ForecastCoverageWindow | null;
  onForecastHourChange: (hour: number) => void;
  onResetToCurrentTime: () => void;
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

export default function ForecastTimeline({ mapOverlays, forecastHour, forecastTimes, forecastHours, activeGlobalValidTime, globalPrecipitationSource, globalCloudSource, globalWindSource, globalTemperatureSource, globalPressureSource, globalWeatherStatuses, globalWeatherCatalog, catalogueCheck, weatherCoverage, onForecastHourChange, onResetToCurrentTime, isPlaying, onPlayingChange }: ForecastTimelineProps) {
  const precipActive = mapOverlays.precipitation && globalPrecipitationSource !== null;
  const cloudActive = mapOverlays.clouds && globalCloudSource !== null;
  const windActive = mapOverlays.windFlow && globalWindSource !== null;
  const temperatureActive = mapOverlays.temperatureContours && globalTemperatureSource !== null;
  const pressureActive = mapOverlays.pressureIsobars && globalPressureSource !== null;
  const hasOverlay = Object.values(mapOverlays).some(Boolean);
  const globalActive = precipActive || cloudActive || windActive || temperatureActive || pressureActive;
  const precipitationStep = globalPrecipitationSource ? getScalarTimestepAtTime(globalPrecipitationSource, activeGlobalValidTime) : null;
  const globalLoading = Object.values(globalWeatherStatuses).some((status) => status === "loading");
  const maximumIndex = Math.max(0, forecastTimes.length - 1);
  const displayedForecastHour = forecastHours?.[forecastHour] ?? forecastHour;
  const forecastLabel = formatForecastTime(forecastTimes[forecastHour]);
  const referenceSource = globalPrecipitationSource ?? globalCloudSource ?? globalWindSource ?? globalTemperatureSource ?? globalPressureSource;
  const resolutionDegrees = referenceSource?.manifest.field?.nativeResolution?.longitudeDegrees ??
    (globalWeatherCatalog?.product.includes("0p25") ? 0.25 : null);

  return <section className="location-timeline workspace-card" aria-label="Forecast timeline">
    <div className="forecast-data-row">
      <WeatherFreshness catalog={globalWeatherCatalog} check={catalogueCheck} coverage={weatherCoverage} compact resolutionDegrees={resolutionDegrees} />
      <details className="map-data-details forecast-data-details">
        <summary aria-label="More forecast data information" title="More forecast data information">i</summary>
        <div className="map-data-popover desktop-surface">
          <p className="map-data-status">{globalActive ? `GFS +${displayedForecastHour}h${precipActive && precipitationStep ? ` · Rain ${accumulationIntervalLabel(precipitationStep)}` : ""}` : globalLoading ? "Loading GFS metadata" : "No global weather overlay selected"}</p>
          {hasOverlay && <LayerLegend mapOverlays={mapOverlays} globalPrecipitationActive={precipActive} precipitationAccumulationHours={precipitationStep?.accumulationHours} />}
          {mapOverlays.pressureIsobars && globalPressureSource && (
            <p className="pressure-note">GFS 0.25° global mean sea-level pressure · instantaneous field.</p>
          )}
          {mapOverlays.pressureIsobars && !globalPressureSource && (
            <p className="status-message error">GFS pressure is unavailable.</p>
          )}
        </div>
      </details>
    </div>
    <div className="location-timeline-heading">
      <div><p className="section-kicker">Forecast time</p><strong>{forecastLabel}</strong></div>
      <span>+{displayedForecastHour}h</span>
    </div>
    <div className="location-timeline-controls">
      <button type="button" className="forecast-play-button" aria-label={isPlaying ? "Pause forecast" : "Play forecast"} aria-pressed={isPlaying} onClick={() => onPlayingChange(!isPlaying)}>{isPlaying ? "Ⅱ" : "▶"}</button>
      <input className="time-slider" type="range" aria-label="Forecast hour" min="0" max={maximumIndex} step="1" value={forecastHour} onChange={(event) => onForecastHourChange(Number(event.target.value))} />
      <button type="button" className="forecast-reset-button" aria-label="Reset to current time" title="Reset to current time" onClick={onResetToCurrentTime}>↻</button>
    </div>
  </section>;
}
