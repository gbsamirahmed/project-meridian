import ForecastDetails from "./ForecastDetails";
import RouteProfile from "./RouteProfile";
import { ROUTE_CONDITION_LEGENDS } from "../services/routeConditionStyle";
import { ANALYSIS_MODES } from "../services/desktopControlOptions";
import type { JourneySchedule, TerrainRoute } from "../types/route";
import type { RouteConditionMode, RouteConditions, RouteConditionStatus } from "../types/routeConditions";

interface RouteAnalysisProps {
  route: TerrainRoute;
  schedule: JourneySchedule | null;
  conditions: RouteConditions | null;
  conditionStatus: RouteConditionStatus;
  conditionMode: RouteConditionMode;
  focusedIndex: number | null;
  pinnedIndex: number | null;
  onPreviewChange: (index: number | null) => void;
  onPinnedChange: (index: number | null) => void;
  onConditionModeChange: (mode: RouteConditionMode) => void;
}

export default function RouteAnalysis({ route, schedule, conditions, conditionStatus, conditionMode, focusedIndex, pinnedIndex, onPreviewChange, onPinnedChange, onConditionModeChange }: RouteAnalysisProps) {
  const legend = conditionMode === "none" ? null : ROUTE_CONDITION_LEGENDS[conditionMode];
  const focusedSample = focusedIndex === null ? null : conditions?.samples[Math.max(0, Math.min(conditions.samples.length - 1, focusedIndex))] ?? null;
  const noteworthyStatus = conditionStatus === "loading" ? "Loading conditions" : conditionStatus === "partial" ? "Partial forecast" : conditionStatus === "unavailable" ? "Weather unavailable" : null;

  return <div className="analysis-workspace" role="region" aria-label="Route analysis">
    <header className="analysis-workspace-heading">
      <div><p className="section-kicker">Route analysis</p><h2 title={route.name}>{route.name}</h2></div>
      {noteworthyStatus && <span className={`analysis-status analysis-status-${conditionStatus}`}>{noteworthyStatus}</span>}
    </header>

    <section className="analysis-profile-card">
      <RouteProfile wide route={route} schedule={schedule} conditions={conditions} conditionMode={conditionMode} focusedIndex={focusedIndex} pinnedIndex={pinnedIndex} onFocusChange={onPreviewChange} onPreviewChange={onPreviewChange} onPinnedChange={onPinnedChange} />
    </section>

    <div className="analysis-mode-controls analysis-workspace-modes" role="group" aria-label="Analysis mode">
      {ANALYSIS_MODES.map(({ mode, label }) => <button key={mode} type="button" title={`${label} analysis`} aria-label={`${label} analysis`} aria-pressed={conditionMode === mode} onClick={() => onConditionModeChange(mode)}>{label}</button>)}
    </div>
    {legend && <div className="route-condition-legend analysis-workspace-legend"><span>{legend.label} · {legend.units}</span><i style={{ background: legend.gradient }} /><div>{legend.values.map((value) => <em key={value}>{value}</em>)}</div></div>}

    <section className="analysis-detail-card">
      {focusedSample ? <ForecastDetails sample={focusedSample} derived={conditions?.derived ?? null} /> : <div className="route-point-empty"><p className="section-kicker">Journey point details</p><h3>Preview or pin a point</h3><p>Move across the profile to preview. Click to keep a point selected.</p></div>}
    </section>
  </div>;
}
