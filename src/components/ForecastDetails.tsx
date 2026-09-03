import DerivedConditionContext from "./DerivedConditionContext";
import { atmosphericHeightLabel, gustLabel, visibilityLabel } from "../services/atmosphericFormatting";
import { precipitationAmountLabel } from "../services/precipitationStyle";
import { accumulationIntervalLabel, routeConditionTimeLabel } from "../services/weatherTimeLabel";
import { timeLabel } from "../services/journeyPresentation";
import type { DerivedRouteConditions } from "../types/derivedRouteConditions";
import type { RouteConditionSample, ScalarRouteCondition } from "../types/routeConditions";

function scalarLabel(condition: ScalarRouteCondition, formatter: (value: number) => string): string {
  if (condition.state === "available") return formatter(condition.value);
  return condition.reason === "outside-forecast" ? "Outside forecast horizon" : "Unavailable";
}

function windDirectionLabel(degrees: number | null): string {
  if (degrees === null) return "Calm";
  const directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  return `${directions[Math.round(degrees / 45) % directions.length]} (from)`;
}

export default function ForecastDetails({ sample, derived }: { sample: RouteConditionSample; derived: DerivedRouteConditions | null }) {
  const sharedProvenance = Object.values(sample.weather).find((condition) => condition.state === "available")?.provenance ?? null;
  const context = derived?.samples[sample.routeSampleIndex] ?? null;
  return (
    <div className="forecast-details">
      <div className="forecast-details-heading"><div><p className="section-kicker">Selected journey point</p><h3>{(sample.cumulativeDistanceM / 1000).toFixed(1)} km · {timeLabel(sample.journey.expectedArrivalTime)}</h3></div><span>{sample.terrain.elevationM === null ? "Elevation unavailable" : `${Math.round(sample.terrain.elevationM)} m`}</span></div>
      <p className="arrival-range">Arrival range {timeLabel(sample.journey.earliestArrivalTime)}–{timeLabel(sample.journey.latestArrivalTime)}</p>
      {context && <DerivedConditionContext raw={sample} context={context} />}
      <div className="forecast-values-grid">
        <span>Temperature</span><strong>{scalarLabel(sample.weather.temperature, (value) => `${value.toFixed(1)} °C`)}</strong>
        <span>Precipitation</span><strong>{scalarLabel(sample.weather.precipitation, precipitationAmountLabel)}{sample.weather.precipitation.state === "available" && <small>{accumulationIntervalLabel(sample.weather.precipitation.provenance)}</small>}</strong>
        <span>Cloud</span><strong>{scalarLabel(sample.weather.cloud, (value) => `${Math.round(value)}%`)}</strong>
        <span>Wind</span><strong>{sample.weather.wind.state === "available" ? `${gustLabel(sample.weather.wind.speedMs)} · ${windDirectionLabel(sample.weather.wind.directionFromDegrees)}` : "Unavailable"}</strong>
        <span>Gusts</span><strong>{scalarLabel(sample.weather.gust, gustLabel)}</strong>
        <span>Visibility</span><strong>{scalarLabel(sample.weather.visibility, visibilityLabel)}</strong>
        <span>Freezing level</span><strong>{scalarLabel(sample.weather.freezingLevel, atmosphericHeightLabel)}</strong>
        <span>Highest freezing level</span><strong>{scalarLabel(sample.weather.highestFreezingLevel, atmosphericHeightLabel)}</strong>
        <span>Cloud ceiling</span><strong>{scalarLabel(sample.weather.cloudCeiling, atmosphericHeightLabel)}</strong>
      </div>
      {sharedProvenance && <div className="shared-source-block"><strong>GFS · {sharedProvenance.nativeResolutionDegrees}° · run {new Date(sharedProvenance.runTime).toLocaleDateString("en-GB", { day: "2-digit", month: "short", timeZone: "UTC" })} {new Date(sharedProvenance.runTime).getUTCHours().toString().padStart(2, "0")}Z</strong><span>{routeConditionTimeLabel(sharedProvenance)}</span></div>}
      <details className="about-data-details"><summary>About this data</summary><p>Weather uses expected arrival only, not the full arrival range. Dense route sampling does not increase GFS 0.25° resolution. Model visibility is not exact local sight distance. Cloud ceiling is above the model surface; no ceiling may mean no diagnosed ceiling or missing data. Gust direction is unavailable, so directional context comes from sustained wind. Freezing levels do not predict ice.</p></details>
    </div>
  );
}
