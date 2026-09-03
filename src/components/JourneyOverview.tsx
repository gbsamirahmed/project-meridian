import { type ChangeEvent, useMemo } from "react";
import { atmosphericHeightLabel, gustLabel, visibilityLabel } from "../services/atmosphericFormatting";
import { freezingSummaryLabel } from "../services/derivedConditionFormatting";
import { combinedCoverageMessages, durationLabel, timeLabel } from "../services/journeyPresentation";
import { precipitationAmountLabel } from "../services/precipitationStyle";
import type { JourneyPlan, JourneyProfile, JourneySchedule, ResampledRouteGeometry, RoutePreparationStatus, TerrainRoute } from "../types/route";
import type { RouteConditions, RouteConditionStatus } from "../types/routeConditions";

interface JourneyOverviewProps {
  routeGeometry: ResampledRouteGeometry | null;
  terrainRoute: TerrainRoute | null;
  schedule: JourneySchedule | null;
  scheduleError: string | null;
  status: RoutePreparationStatus;
  statusMessage: string | null;
  profile: JourneyProfile;
  plan: JourneyPlan;
  routeConditions: RouteConditions | null;
  routeConditionStatus: RouteConditionStatus;
  onImport: (file: File) => void;
  onClear: () => void;
  onOpenSettings: () => void;
  onOpenAnalysis: () => void;
}

export default function JourneyOverview({ routeGeometry, terrainRoute, schedule, scheduleError, status, statusMessage, profile, plan, routeConditions, routeConditionStatus, onImport, onClear, onOpenSettings, onOpenAnalysis }: JourneyOverviewProps) {
  const handleFile = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (file) onImport(file);
  };
  const coverageMessages = useMemo(() => routeConditions ? combinedCoverageMessages(routeConditions) : [], [routeConditions]);
  const gradients = terrainRoute?.samples.map((sample) => sample.gradient).filter((value): value is number => value !== null) ?? [];
  const steepestGradient = gradients.length ? Math.max(...gradients.map(Math.abs)) : null;

  if (!routeGeometry) {
    return (
      <section className="workspace-card journey-empty">
        <p className="section-kicker">Journey</p>
        <h2>Plan with a route</h2>
        <p>Import a GPX to connect terrain, a walking schedule, and weather at expected arrival times.</p>
        <label className="route-import-button"><input type="file" accept=".gpx,application/gpx+xml" onChange={handleFile} />Import GPX</label>
        <small>Processed in this browser; the file is not uploaded.</small>
      </section>
    );
  }

  return (
    <div className="journey-overview">
      <div className="journey-title-row">
        <div><p className="section-kicker">Journey overview</p><h2 title={routeGeometry.name}>{routeGeometry.name}</h2></div>
        <button type="button" className="route-clear-button" onClick={onClear}>Clear route</button>
      </div>
      <div className={`route-status route-status-${status}`}><span aria-hidden="true" />{statusMessage ?? (status === "ready" ? "Terrain and timing ready" : "Preparing route")}</div>

      <section className="journey-section route-facts-section">
        <div className="journey-section-heading"><div><p className="section-kicker">Route facts</p><h3>Measured from route & terrain</h3></div></div>
        <div className="route-facts-grid">
          <div><span>Distance</span><strong>{(routeGeometry.totalDistanceM / 1000).toFixed(1)} km</strong></div>
          <div><span>Ascent</span><strong>{terrainRoute?.totalAscentM == null ? "—" : `${Math.round(terrainRoute.totalAscentM)} m`}</strong></div>
          <div><span>Descent</span><strong>{terrainRoute?.totalDescentM == null ? "—" : `${Math.round(terrainRoute.totalDescentM)} m`}</strong></div>
        </div>
      </section>

      <section className="journey-section journey-estimate-section">
        <div className="journey-section-heading"><div><p className="section-kicker">Journey estimate</p><h3>{schedule ? `About ${durationLabel(schedule.totalMinutes)}` : "Awaiting complete terrain"}</h3></div><button type="button" className="tune-button" onClick={onOpenSettings}>Tune</button></div>
        {schedule && <>
          <div className="estimate-detail-row"><span>Moving {durationLabel(schedule.movingMinutes)}</span><span>Breaks {durationLabel(schedule.stoppedMinutes)}</span></div>
          <p className="journey-time-range">{timeLabel(schedule.departureTime)} → <strong>{timeLabel(schedule.expectedFinishTime)}</strong></p>
          <p className="arrival-range">Likely total {durationLabel(schedule.likelyMinimumMinutes)}–{durationLabel(schedule.likelyMaximumMinutes)}</p>
          {plan.mode !== "profile" && <p className={`route-pace-comparison route-pace-${schedule.targetComparison}`}>{schedule.targetComparison === "close-to-baseline" ? "Close to selected baseline" : schedule.targetComparison === "faster-than-baseline" ? "Faster than selected baseline" : "Slower than selected baseline"}</p>}
        </>}
        <small>{profile.pace} pace · {profile.party} · {profile.load === "light" ? "day pack" : "overnight load"}</small>
      </section>

      {(scheduleError || status === "partial" || status === "error") && <p className="route-error">{scheduleError ?? statusMessage}</p>}

      <section className="journey-section journey-weather-section">
        <div className="journey-section-heading"><div><p className="section-kicker">Weather overview</p><h3>Along the expected journey</h3></div><button type="button" className="text-button" onClick={onOpenAnalysis}>Open analysis</button></div>
        {routeConditionStatus === "loading" && <p className="muted-copy">Preparing weather along the schedule…</p>}
        {routeConditions ? <>
          <div className="journey-weather-grid">
            <div className="weather-headline-primary"><span>Temperature</span><strong>{routeConditions.summary.temperatureRangeC ? `${routeConditions.summary.temperatureRangeC[0].toFixed(1)}–${routeConditions.summary.temperatureRangeC[1].toFixed(1)} °C` : "Unavailable"}</strong></div>
            {routeConditions.summary.precipitationEncountered && <div><span>Peak rain interval</span><strong>{precipitationAmountLabel(routeConditions.summary.precipitationMaximumMm!)}</strong></div>}
            {routeConditions.summary.gustMaximumMs !== null && <div><span>Peak gust</span><strong>{gustLabel(routeConditions.summary.gustMaximumMs)}</strong></div>}
            {routeConditions.summary.visibilityMinimumM !== null && <div><span>Lowest visibility</span><strong>{visibilityLabel(routeConditions.summary.visibilityMinimumM)}</strong></div>}
            {routeConditions.summary.gustMaximumMs === null && routeConditions.summary.windMaximumMs !== null && <div><span>Peak sustained wind</span><strong>{gustLabel(routeConditions.summary.windMaximumMs)}</strong></div>}
          </div>
          {coverageMessages.length > 0 && <div className="coverage-messages">{coverageMessages.map((message) => <p key={message}>{message}</p>)}</div>}
        </> : routeConditionStatus !== "loading" ? <p className="muted-copy">Weather will appear when a complete schedule is available.</p> : null}
      </section>

      <section className="journey-section terrain-overview-section">
        <p className="section-kicker">Terrain overview</p>
        <div className="terrain-overview-row"><div><h3>{terrainRoute?.elevationCoverage === "complete" ? "Elevation profile ready" : "Limited terrain coverage"}</h3><p>{steepestGradient === null ? "Gradient unavailable" : `Steepest sampled gradient ${(steepestGradient * 100).toFixed(0)}%`}</p></div><button type="button" className="text-button" onClick={onOpenAnalysis}>View profile</button></div>
        {routeConditions?.derived && <details className="compact-details"><summary>Freezing context</summary><p>{freezingSummaryLabel(routeConditions.derived)}</p>{routeConditions.summary.freezingLevelRangeGpm && <small>Forecast 0°C level {atmosphericHeightLabel(routeConditions.summary.freezingLevelRangeGpm[0])}–{atmosphericHeightLabel(routeConditions.summary.freezingLevelRangeGpm[1])}.</small>}</details>}
      </section>
    </div>
  );
}
