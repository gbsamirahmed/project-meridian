import { useEffect, useState } from "react";
import LayerLegend from "./LayerLegend";
import LayerPanel from "./LayerPanel";
import TimeSlider from "./TimeSlider";
import WeatherFreshness from "./WeatherFreshness";
import { accumulationIntervalLabel } from "../services/weatherTimeLabel";
import { getScalarTimestepAtTime, getVectorTimestepAtTime } from "../services/globalWeatherService";
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
  onClose: () => void;
}

export default function MapControls({ basemap, mapOverlays, satelliteAvailable, forecastHour, forecastTimes, forecastHours, activeGlobalValidTime, globalPrecipitationSource, globalCloudSource, globalWindSource, globalTemperatureSource, globalWeatherStatuses, globalWeatherCatalog, catalogueCheck, journeySchedule, weatherGridStatus, onBasemapChange, onOverlayChange, onForecastHourChange, onClose }: MapControlsProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  useEffect(() => {
    if (!isPlaying || forecastTimes.length < 2) return;
    const interval = window.setInterval(() => onForecastHourChange(forecastHour >= forecastTimes.length - 1 ? 0 : forecastHour + 1), 500);
    return () => window.clearInterval(interval);
  }, [isPlaying, forecastHour, forecastTimes.length, onForecastHourChange]);

  const precipActive = mapOverlays.precipitation && globalPrecipitationSource !== null;
  const cloudActive = mapOverlays.clouds && globalCloudSource !== null;
  const windActive = mapOverlays.windFlow && globalWindSource !== null;
  const temperatureActive = mapOverlays.temperatureContours && globalTemperatureSource !== null;
  const globalActive = precipActive || cloudActive || windActive || temperatureActive;
  const precipitationStep = globalPrecipitationSource ? getScalarTimestepAtTime(globalPrecipitationSource, activeGlobalValidTime) : null;
  const cloudStep = globalCloudSource ? getScalarTimestepAtTime(globalCloudSource, activeGlobalValidTime) : null;
  const windStep = globalWindSource ? getVectorTimestepAtTime(globalWindSource, activeGlobalValidTime) : null;
  const temperatureStep = globalTemperatureSource ? getScalarTimestepAtTime(globalTemperatureSource, activeGlobalValidTime) : null;
  const globalLoading = Object.values(globalWeatherStatuses).some((status) => status === "loading");

  return (
    <aside className="map-controls desktop-surface" aria-label="Map controls">
      <div className="map-controls-heading"><div><p className="section-kicker">Map controls</p><h2>Display & forecast</h2></div><button type="button" aria-label="Hide map controls" onClick={onClose}>×</button></div>
      <WeatherFreshness catalog={globalWeatherCatalog} check={catalogueCheck} journey={journeySchedule} />
      <LayerPanel basemap={basemap} mapOverlays={mapOverlays} satelliteAvailable={satelliteAvailable} onBasemapChange={onBasemapChange} onOverlayChange={onOverlayChange} />
      <TimeSlider forecastHour={forecastHour} forecastTimes={forecastTimes} forecastHours={forecastHours} sourceLabel={globalActive ? `GFS valid-time steps${precipActive && precipitationStep ? ` · Rain: ${accumulationIntervalLabel(precipitationStep)}` : ""}` : undefined} onForecastHourChange={onForecastHourChange} />
      <div className="map-play-row"><button type="button" className="play-button" onClick={() => setIsPlaying((current) => !current)}><span aria-hidden="true">{isPlaying ? "Ⅱ" : "▶"}</span>{isPlaying ? "Pause" : "Play forecast"}</button><span>{globalActive ? `GFS +${precipitationStep?.forecastHour ?? cloudStep?.forecastHour ?? windStep?.forecastHour ?? temperatureStep?.forecastHour ?? 0}h` : globalLoading ? "Loading GFS metadata" : `Regional pressure · 9 × 9 samples${weatherGridStatus === "error" ? " · unavailable" : ""}`}</span></div>
      <details className="map-legend-details"><summary>Layer legend</summary><LayerLegend mapOverlays={mapOverlays} globalPrecipitationActive={precipActive} precipitationAccumulationHours={precipitationStep?.accumulationHours} /></details>
      {mapOverlays.pressureIsobars && <p className="pressure-note">Pressure is the remaining regional Open-Meteo field. The 9 × 9 samples describe that pressure grid only.</p>}
    </aside>
  );
}
