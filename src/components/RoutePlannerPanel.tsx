import type { ChangeEvent } from "react";
import RouteProfile from "./RouteProfile";
import type {
  JourneyPlan,
  JourneyProfile,
  JourneySchedule,
  ResampledRouteGeometry,
  RoutePreparationStatus,
  TerrainRoute,
} from "../types/route";

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
  onImport: (file: File) => void;
  onClear: () => void;
  onProfileChange: (profile: JourneyProfile) => void;
  onPlanChange: (plan: JourneyPlan) => void;
  onFocusChange: (index: number | null) => void;
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
  onImport,
  onClear,
  onProfileChange,
  onPlanChange,
  onFocusChange,
}: RoutePlannerPanelProps) {
  const handleFile = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    onImport(file);
  };
  const route = terrainRoute;
  return (
    <section className="weather-card route-planner-card">
      <div className="card-heading">
        <div>
          <p className="section-kicker">Journey planning</p>
          <h2>{routeGeometry?.name ?? "Route foundation"}</h2>
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
            <RouteProfile route={route} schedule={schedule} focusedIndex={focusedIndex} onFocusChange={onFocusChange} />
          )}
        </>
      )}
    </section>
  );
}
