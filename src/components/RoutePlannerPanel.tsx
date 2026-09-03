import { useMemo, type ChangeEvent } from "react";
import RouteProfile from "./RouteProfile";
import DerivedConditionContext from "./DerivedConditionContext";
import { crossingLabel, freezingSummaryLabel } from "../services/derivedConditionFormatting";
import { ROUTE_CONDITION_LEGENDS } from "../services/routeConditionStyle";
import { accumulationIntervalLabel, routeConditionTimeLabel } from "../services/weatherTimeLabel";
import { precipitationAmountLabel } from "../services/precipitationStyle";
import { gustLabel, visibilityLabel, atmosphericHeightLabel, fieldCoverageLabel } from "../services/atmosphericFormatting";
import type {
  JourneyPlan,
  JourneyProfile,
  JourneySchedule,
  ResampledRouteGeometry,
  RoutePreparationStatus,
  TerrainRoute,
} from "../types/route";
import type {
  RouteConditionMode,
  RouteConditions,
  RouteConditionStatus,
  ScalarRouteCondition,
} from "../types/routeConditions";

interface RoutePlannerPanelProps {
  routeGeometry: ResampledRouteGeometry | null;
  terrainRoute: TerrainRoute | null;
  schedule: JourneySchedule | null;
  scheduleError: string | null;
  status: RoutePreparationStatus;
  statusMessage: string | null;
  profile: JourneyProfile;
  plan: JourneyPlan;
  focusedIndex: number | null;
  routeConditions: RouteConditions | null;
  routeConditionStatus: RouteConditionStatus;
  routeConditionMode: RouteConditionMode;
  onImport: (file: File) => void;
  onClear: () => void;
  onProfileChange: (profile: JourneyProfile) => void;
  onPlanChange: (plan: JourneyPlan) => void;
  onFocusChange: (index: number | null) => void;
  onRouteConditionModeChange: (mode: RouteConditionMode) => void;
}

function durationLabel(minutes: number): string {
  const rounded = Math.max(0, Math.round(minutes / 5) * 5);
  const hours = Math.floor(rounded / 60);
  const remainder = rounded % 60;
  return hours ? `${hours} h${remainder ? ` ${remainder} min` : ""}` : `${remainder} min`;
}

function timeLabel(iso: string): string {
  return new Intl.DateTimeFormat(undefined, {
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
}

function localInputValue(iso: string): string {
  const date = new Date(iso);
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 16);
}

function isoFromLocal(value: string, fallback: string): string {
  const parsed = new Date(value);
  return Number.isFinite(parsed.getTime()) ? parsed.toISOString() : fallback;
}

function scalarLabel(
  condition: ScalarRouteCondition,
  formatter: (value: number) => string
): string {
  return condition.state === "available" ? formatter(condition.value) : "Unavailable";
}

function windDirectionLabel(degrees: number | null): string {
  if (degrees === null) return "Calm";
  const directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  return `${directions[Math.round(degrees / 45) % directions.length]} (from)`;
}

export default function RoutePlannerPanel({
  routeGeometry,
  terrainRoute,
  schedule,
  scheduleError,
  status,
  statusMessage,
  profile,
  plan,
  focusedIndex,
  routeConditions,
  routeConditionStatus,
  routeConditionMode,
  onImport,
  onClear,
  onProfileChange,
  onPlanChange,
  onFocusChange,
  onRouteConditionModeChange,
}: RoutePlannerPanelProps) {
  const handleFile = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    onImport(file);
  };
  const route = terrainRoute;
  const derived = routeConditions?.derived;
  const focusedCondition =
    focusedIndex === null
      ? null
      : routeConditions?.samples[
          Math.max(0, Math.min(routeConditions.samples.length - 1, focusedIndex))
        ] ?? null;
  const legend =
    routeConditionMode === "none"
      ? null
      : ROUTE_CONDITION_LEGENDS[routeConditionMode];
  const focusedProvenance = focusedCondition
    ? [
        routeConditionMode === "temperature"
          ? focusedCondition.weather.temperature
          : routeConditionMode === "precipitation"
            ? focusedCondition.weather.precipitation
            : routeConditionMode === "wind"
              ? focusedCondition.weather.wind
              : null,
        focusedCondition.weather.temperature,
        focusedCondition.weather.precipitation,
        focusedCondition.weather.wind,
        focusedCondition.weather.cloud,
      ].find((condition) => condition?.state === "available")?.provenance ?? null
    : null;
  const allWeatherOutsideForecast = useMemo(
    () =>
      Boolean(
        routeConditions?.samples.length &&
          routeConditions.samples.every((sample) =>
            Object.values(sample.weather).every(
              (condition) =>
                condition.state === "unavailable" &&
                condition.reason === "outside-forecast"
            )
          )
      ),
    [routeConditions]
  );
  return (
    <section className="weather-card route-planner-card">
      <div className="card-heading">
        <div>
          <p className="section-kicker">Journey planning</p>
          <h2>{routeGeometry?.name ?? "Plan a journey"}</h2>
        </div>
        {routeGeometry && (
          <button type="button" className="route-clear-button" onClick={onClear}>
            Clear
          </button>
        )}
      </div>
      {!routeGeometry ? (
        <div className="route-import-state">
          <p>Import a local GPX to analyse its terrain and estimated walking schedule.</p>
          <label className="route-import-button">
            <input type="file" accept=".gpx,application/gpx+xml" onChange={handleFile} />
            Import GPX
          </label>
          <small>Processed in this browser; the file is not uploaded.</small>
        </div>
      ) : (
        <>
          <div className={`route-status route-status-${status}`}>
            <span aria-hidden="true" />
            {statusMessage ?? (status === "ready" ? "Terrain and timing ready" : "Preparing route")}
          </div>
          <div className="route-summary-grid">
            <div><span>Distance</span><strong>{(routeGeometry.totalDistanceM / 1000).toFixed(1)} km</strong></div>
            <div><span>Ascent</span><strong>{route?.totalAscentM === null || route?.totalAscentM === undefined ? "—" : `${Math.round(route.totalAscentM)} m`}</strong></div>
            <div><span>Descent</span><strong>{route?.totalDescentM === null || route?.totalDescentM === undefined ? "—" : `${Math.round(route.totalDescentM)} m`}</strong></div>
            <div><span>Expected</span><strong>{schedule ? `About ${durationLabel(schedule.totalMinutes)}` : "—"}</strong></div>
            <div><span>Moving</span><strong>{schedule ? durationLabel(schedule.movingMinutes) : "—"}</strong></div>
            <div><span>Breaks</span><strong>{durationLabel(profile.plannedBreakMinutes)}</strong></div>
          </div>
          {schedule && (
            <div className="route-condition-controls">
              <label>
                <span>Journey route colour</span>
                <select
                  value={routeConditionMode}
                  onChange={(event) =>
                    onRouteConditionModeChange(
                      event.target.value as RouteConditionMode
                    )
                  }
                >
                  <option value="none">Normal route</option>
                  <option value="temperature">Temperature</option>
                  <option value="precipitation">Precipitation</option>
                  <option value="wind">Wind</option>
                  <option value="gradient">Gradient</option>
                </select>
              </label>
              <small>
                {routeConditionStatus === "loading"
                  ? "Preparing journey conditions…"
                  : routeConditionStatus === "ready"
                    ? "Conditions use weather at each expected arrival time."
                    : routeConditionStatus === "partial"
                      ? "Some journey weather is unavailable or outside the forecast horizon."
                      : routeConditionStatus === "unavailable"
                        ? allWeatherOutsideForecast
                          ? "Journey times are outside the available GFS forecast horizon."
                          : "Journey weather is unavailable; terrain and timing remain usable."
                        : "Journey conditions await a complete schedule."}
              </small>
              {legend && (
                <div className="route-condition-legend">
                  <span>{legend.label} · {legend.units}</span>
                  <i style={{ background: legend.gradient }} />
                  <div>
                    {legend.values.map((value) => <em key={value}>{value}</em>)}
                  </div>
                </div>
              )}
            </div>
          )}
          {routeConditions && (
            <div className="route-condition-summary">
              <div>
                <span>Temperature</span>
                <strong>
                  {routeConditions.summary.temperatureRangeC
                    ? `${routeConditions.summary.temperatureRangeC[0].toFixed(1)}–${routeConditions.summary.temperatureRangeC[1].toFixed(1)} °C`
                    : "Unavailable"}
                </strong>
              </div>
              <div>
                <span>Peak wind</span>
                <strong>
                  {routeConditions.summary.windMaximumMs === null
                    ? "Unavailable"
                    : `${(routeConditions.summary.windMaximumMs * 3.6).toFixed(1)} km/h`}
                </strong>
              </div>
              <div>
                <span>Precipitation</span>
                <strong>
                  {routeConditions.summary.precipitationEncountered === null
                    ? "Unavailable"
                    : routeConditions.summary.precipitationEncountered
                      ? `Up to ${precipitationAmountLabel(routeConditions.summary.precipitationMaximumMm!)}`
                      : routeConditions.coverage.precipitation.availableSamples ===
                          routeConditions.coverage.precipitation.totalSamples
                        ? "No interval rain"
                        : "None in available samples"}
                </strong>
              </div>
              <div>
                <span>Peak gust · available samples</span>
                <strong>{routeConditions.summary.gustMaximumMs === null ? "Unavailable" : gustLabel(routeConditions.summary.gustMaximumMs)}</strong>
                <small>{fieldCoverageLabel(routeConditions.coverage.gust)}</small>
              </div>
              <div>
                <span>Lowest model visibility</span>
                <strong>{routeConditions.summary.visibilityMinimumM === null ? "Unavailable" : visibilityLabel(routeConditions.summary.visibilityMinimumM)}</strong>
                <small>{fieldCoverageLabel(routeConditions.coverage.visibility)}</small>
              </div>
            </div>
          )}
          {derived && (
            <div className="route-derived-summary">
              <p>{freezingSummaryLabel(derived)}</p>
              {derived.summary.freezingCrossings > 0 && <details className="route-assumptions">
                <summary>{derived.summary.freezingCrossings} forecast 0°C-level transition(s)</summary>
                {derived.events.filter(event => event.kind === "freezing-crossing").map((event, index) => (
                  <button type="button" className="route-event-button" key={index} onClick={() => onFocusChange(event.toSampleIndex)}>{crossingLabel(event)}</button>
                ))}
              </details>}
              <details className="route-assumptions">
                <summary>Wind context across available samples</summary>
                <p>Strongest sustained crosswind {routeConditions!.summary.crosswindMaximumMs === null ? "unavailable" : gustLabel(routeConditions!.summary.crosswindMaximumMs)} · headwind {routeConditions!.summary.headwindMaximumMs === null ? "unavailable" : gustLabel(routeConditions!.summary.headwindMaximumMs)}.</p>
                <small>{fieldCoverageLabel(derived.coverage.wind)} · regional wind, not terrain-downscaled airflow.</small>
              </details>
            </div>
          )}
          {schedule && (
            <div className="route-estimate-copy">
              <strong>Finish {timeLabel(schedule.expectedFinishTime)}</strong>
              <span>
                Likely roughly {durationLabel(schedule.likelyMinimumMinutes)} – {durationLabel(schedule.likelyMaximumMinutes)}
              </span>
              {plan.mode !== "profile" && (
                <span className={`route-pace-comparison route-pace-${schedule.targetComparison}`}>
                  {schedule.targetComparison === "close-to-baseline"
                    ? "Close to selected baseline"
                    : schedule.targetComparison === "faster-than-baseline"
                      ? "Faster than selected baseline"
                      : "Slower than selected baseline"}
                </span>
              )}
            </div>
          )}
          {(scheduleError || status === "partial" || status === "error") && (
            <p className="route-error">{scheduleError ?? statusMessage}</p>
          )}
          <details className="route-assumptions">
            <summary>Journey assumptions</summary>
            <div className="route-form-grid">
              <label>
                <span>Activity</span>
                <strong>Hiking / walking</strong>
              </label>
              <label>
                <span>Pace</span>
                <select value={profile.pace} onChange={(event) => onProfileChange({ ...profile, pace: event.target.value as JourneyProfile["pace"] })}>
                  <option value="relaxed">Relaxed</option>
                  <option value="normal">Normal</option>
                  <option value="fast">Fast</option>
                </select>
              </label>
              <label>
                <span>Party</span>
                <select value={profile.party} onChange={(event) => onProfileChange({ ...profile, party: event.target.value as JourneyProfile["party"] })}>
                  <option value="solo">Solo</option>
                  <option value="group">Group</option>
                </select>
              </label>
              <label>
                <span>Load</span>
                <select value={profile.load} onChange={(event) => onProfileChange({ ...profile, load: event.target.value as JourneyProfile["load"] })}>
                  <option value="light">Light / day pack</option>
                  <option value="heavy">Heavy / overnight</option>
                </select>
              </label>
              <label>
                <span>Planned breaks</span>
                <select value={profile.plannedBreakMinutes} onChange={(event) => onProfileChange({ ...profile, plannedBreakMinutes: Number(event.target.value) })}>
                  <option value={0}>Minimal / none</option>
                  <option value={30}>Normal · 30 min</option>
                  <option value={60}>Generous · 60 min</option>
                </select>
              </label>
              <label>
                <span>Plan from</span>
                <select value={plan.mode} onChange={(event) => onPlanChange({ ...plan, mode: event.target.value as JourneyPlan["mode"] })}>
                  <option value="profile">Selected profile</option>
                  <option value="target-duration">Target duration</option>
                  <option value="target-finish">Target finish</option>
                </select>
              </label>
              <label className="route-form-wide">
                <span>Departure</span>
                <input type="datetime-local" value={localInputValue(plan.departureTime)} onChange={(event) => onPlanChange({ ...plan, departureTime: isoFromLocal(event.target.value, plan.departureTime) })} />
              </label>
              {plan.mode === "target-duration" && (
                <label className="route-form-wide">
                  <span>Target total hours</span>
                  <input type="number" min="0.5" max="48" step="0.25" value={(plan.targetDurationMinutes / 60).toFixed(2)} onChange={(event) => onPlanChange({ ...plan, targetDurationMinutes: Number(event.target.value) * 60 })} />
                </label>
              )}
              {plan.mode === "target-finish" && (
                <label className="route-form-wide">
                  <span>Target finish</span>
                  <input type="datetime-local" value={localInputValue(plan.targetFinishTime)} onChange={(event) => onPlanChange({ ...plan, targetFinishTime: isoFromLocal(event.target.value, plan.targetFinishTime) })} />
                </label>
              )}
            </div>
          </details>
          {route && (
            <RouteProfile
              route={route}
              schedule={schedule}
              conditions={routeConditions}
              conditionMode={routeConditionMode}
              focusedIndex={focusedIndex}
              onFocusChange={onFocusChange}
            />
          )}
          {focusedCondition && (
            <div className="route-condition-inspector">
              <div className="route-condition-inspector-heading">
                <span>Journey conditions</span>
                <strong>
                  {(focusedCondition.cumulativeDistanceM / 1000).toFixed(1)} km · {timeLabel(focusedCondition.journey.expectedArrivalTime)}
                </strong>
              </div>
              <div className="route-condition-inspector-grid">
                <span>Arrival range</span>
                <strong>
                  {timeLabel(focusedCondition.journey.earliestArrivalTime)}–{timeLabel(focusedCondition.journey.latestArrivalTime)}
                </strong>
                <span>Elevation</span>
                <strong>{focusedCondition.terrain.elevationM === null ? "Unavailable" : `${Math.round(focusedCondition.terrain.elevationM)} m`}</strong>
                <span>Gradient</span>
                <strong>{focusedCondition.terrain.gradient === null ? "Unavailable" : `${(focusedCondition.terrain.gradient * 100).toFixed(1)}%`}</strong>
              </div>
              {derived?.samples[focusedCondition.routeSampleIndex] && (
                <DerivedConditionContext raw={focusedCondition} context={derived.samples[focusedCondition.routeSampleIndex]} />
              )}
              <details className="route-assumptions">
                <summary>Raw model values & provenance</summary>
              <div className="route-condition-inspector-grid">
                <span>Temperature</span>
                <strong>{scalarLabel(focusedCondition.weather.temperature, (value) => `${value.toFixed(1)} °C`)}</strong>
                <span>Precipitation</span>
                <strong>
                  {scalarLabel(focusedCondition.weather.precipitation, precipitationAmountLabel)}
                  {focusedCondition.weather.precipitation.state === "available" && (
                    <><br /><small>{accumulationIntervalLabel(focusedCondition.weather.precipitation.provenance)}</small></>
                  )}
                </strong>
                <span>Cloud</span>
                <strong>{scalarLabel(focusedCondition.weather.cloud, (value) => `${Math.round(value)}%`)}</strong>
                <span>Wind</span>
                <strong>
                  {focusedCondition.weather.wind.state === "available"
                    ? `${(focusedCondition.weather.wind.speedMs * 3.6).toFixed(1)} km/h · ${windDirectionLabel(focusedCondition.weather.wind.directionFromDegrees)}`
                    : "Unavailable"}
                </strong>
                <span>Along route</span>
                <strong>
                  {focusedCondition.weather.wind.state === "available" &&
                  focusedCondition.weather.wind.relative
                    ? focusedCondition.weather.wind.relative.alongRouteMs >= 0
                      ? `${(focusedCondition.weather.wind.relative.tailwindMs * 3.6).toFixed(1)} km/h tailwind`
                      : `${(focusedCondition.weather.wind.relative.headwindMs * 3.6).toFixed(1)} km/h headwind`
                    : "Unavailable"}
                </strong>
                <span>Crosswind</span>
                <strong>
                  {focusedCondition.weather.wind.state === "available" &&
                  focusedCondition.weather.wind.relative
                    ? focusedCondition.weather.wind.relative.crosswindFrom === "calm"
                      ? "Calm"
                      : `${(focusedCondition.weather.wind.relative.crosswindMs * 3.6).toFixed(1)} km/h from ${focusedCondition.weather.wind.relative.crosswindFrom}`
                    : "Unavailable"}
                </strong>
              </div>
              <div className="route-condition-inspector-grid">
                <span>Gusts</span>
                <strong>{scalarLabel(focusedCondition.weather.gust, gustLabel)}</strong>
                <span>Model visibility</span>
                <strong>{scalarLabel(focusedCondition.weather.visibility, visibilityLabel)}</strong>
                <span>0°C level · sea level</span>
                <strong>{scalarLabel(focusedCondition.weather.freezingLevel, atmosphericHeightLabel)}</strong>
                <span>Cloud ceiling · experimental</span>
                <strong>{scalarLabel(focusedCondition.weather.cloudCeiling, atmosphericHeightLabel)}</strong>
              </div>
              <small>Ceiling is above the model surface, not sea level. No ceiling value may mean no diagnosed ceiling or missing data. These heights do not indicate ice or cloud immersion.</small>
              <div>
                <p>Highest tropospheric freezing level: {scalarLabel(focusedCondition.weather.highestFreezingLevel, atmosphericHeightLabel)} · sea level</p>
                {([
                  ["Gust", focusedCondition.weather.gust],
                  ["Model visibility", focusedCondition.weather.visibility],
                  ["0°C level", focusedCondition.weather.freezingLevel],
                  ["Highest freezing level", focusedCondition.weather.highestFreezingLevel],
                  ["Cloud ceiling", focusedCondition.weather.cloudCeiling],
                ] as const).map(([label, condition]) => (
                  <p key={label}>
                    <strong>{label}</strong>: {condition.state === "available"
                      ? `GFS ${condition.provenance.nativeResolutionDegrees}° · ${condition.provenance.sourceLevel} · run ${new Date(condition.provenance.runTime).toISOString().slice(0, 13).replace("T", " ")}Z · +${condition.provenance.forecastHour} h · ${routeConditionTimeLabel(condition.provenance)} · ${condition.units}`
                      : condition.reason === "outside-forecast" ? "Outside forecast horizon" : "Unavailable"}
                  </p>
                ))}
                <small>Context uses expected arrival only, not the full arrival range. Instantaneous model diagnostics, not hourly maxima. Dense route samples do not increase GFS 0.25° resolution. Visibility is modelled, not an exact local sight distance. Gust direction is unknown; directional context comes only from sustained wind.</small>
              </div>
              </details>
              {focusedProvenance && (
                <small>
                  GFS 0.25° · run {new Date(focusedProvenance.runTime).getUTCHours().toString().padStart(2, "0")}Z · +{focusedProvenance.forecastHour} h · {routeConditionTimeLabel(focusedProvenance)}
                </small>
              )}
            </div>
          )}
        </>
      )}
    </section>
  );
}
