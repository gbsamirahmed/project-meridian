import DerivedConditionContext from "./DerivedConditionContext";
import { atmosphericHeightLabel, gustLabel, visibilityLabel } from "../services/atmosphericFormatting";
import { precipitationAmountLabel } from "../services/precipitationStyle";
import { accumulationIntervalLabel, routeConditionTimeLabel } from "../services/weatherTimeLabel";
import { timeLabel } from "../services/journeyPresentation";
import type { DerivedRouteConditions } from "../types/derivedRouteConditions";
import type { RouteConditionSample, ScalarRouteCondition, WindRouteCondition } from "../types/routeConditions";

function scalarLabel(condition: ScalarRouteCondition, formatter: (value: number) => string): string {
  if (condition.state === "available") return formatter(condition.value);
  return condition.reason === "outside-forecast" ? "Outside forecast" : "Unavailable";
}

function windLabel(condition: WindRouteCondition): string {
  if (condition.state !== "available") return condition.reason === "outside-forecast" ? "Outside forecast" : "Unavailable";
  if (condition.directionFromDegrees === null) return "Calm";
  const directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  return `${gustLabel(condition.speedMs)} · ${directions[Math.round(condition.directionFromDegrees / 45) % directions.length]} from`;
}

export default function ForecastDetails({ sample, derived }: { sample: RouteConditionSample; derived: DerivedRouteConditions | null }) {
  const sharedProvenance = Object.values(sample.weather).find((condition) => condition.state === "available")?.provenance ?? null;
  const context = derived?.samples[sample.routeSampleIndex] ?? null;
  const allOutsideForecast = Object.values(sample.weather).every(
    (condition) => condition.state === "unavailable" && condition.reason === "outside-forecast"
  );
  const values = [
    ["Temperature", scalarLabel(sample.weather.temperature, (value) => `${value.toFixed(1)} °C`)],
    ["Cloud", scalarLabel(sample.weather.cloud, (value) => `${Math.round(value)}%`)],
    ["Wind", windLabel(sample.weather.wind)],
    ["Gusts", scalarLabel(sample.weather.gust, gustLabel)],
    ["Visibility", scalarLabel(sample.weather.visibility, visibilityLabel)],
    ["Freezing level", scalarLabel(sample.weather.freezingLevel, atmosphericHeightLabel)],
    ["Highest freezing level", scalarLabel(sample.weather.highestFreezingLevel, atmosphericHeightLabel)],
    ["Cloud ceiling", scalarLabel(sample.weather.cloudCeiling, atmosphericHeightLabel)],
  ] as const;

  return (
    <div className="forecast-details">
      <div className="forecast-details-heading">
        <div><p className="section-kicker">Selected journey point</p><h3>{(sample.cumulativeDistanceM / 1000).toFixed(1)} km · {timeLabel(sample.journey.expectedArrivalTime)}</h3></div>
        <span>{sample.terrain.elevationM === null ? "Elevation unavailable" : `${Math.round(sample.terrain.elevationM)} m`}</span>
      </div>
      <p className="arrival-range">Arrival {timeLabel(sample.journey.earliestArrivalTime)}–{timeLabel(sample.journey.latestArrivalTime)}</p>
      {allOutsideForecast ? (
        <p className="outside-forecast-message">Weather at this point is outside the available forecast horizon.</p>
      ) : (
        <div className="forecast-values-grid">
          <div className="forecast-value forecast-value-precipitation">
            <span>Precipitation</span>
            <strong>{scalarLabel(sample.weather.precipitation, precipitationAmountLabel)}</strong>
            {sample.weather.precipitation.state === "available" && <small>{accumulationIntervalLabel(sample.weather.precipitation.provenance)}</small>}
          </div>
          {values.map(([label, value]) => <div className="forecast-value" key={label}><span>{label}</span><strong>{value}</strong></div>)}
        </div>
      )}
      <div className="forecast-detail-foot">
        {sharedProvenance && <div className="shared-source-block"><strong>GFS · {sharedProvenance.nativeResolutionDegrees}° · run {new Date(sharedProvenance.runTime).toLocaleDateString("en-GB", { day: "2-digit", month: "short", timeZone: "UTC" })} {new Date(sharedProvenance.runTime).getUTCHours().toString().padStart(2, "0")}Z</strong><span>{routeConditionTimeLabel(sharedProvenance)}</span></div>}
        {context && <details className="derived-context-details"><summary>Condition context</summary><DerivedConditionContext raw={sample} context={context} /></details>}
        <details className="about-data-details"><summary>About this data</summary><p>Expected-arrival model context only. Dense route sampling does not increase GFS 0.25° resolution. Visibility is not exact local sight distance. Ceiling is above the model surface. Gust direction is unavailable. Freezing levels do not predict ice.</p></details>
      </div>
    </div>
  );
}
