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
  const activeIndex = focusedIndex ?? pinnedIndex ?? 0;
  const focusedSample = conditions?.samples[Math.max(0, Math.min(conditions.samples.length - 1, activeIndex))] ?? null;
  const noteworthyStatus = conditionStatus === "loading" ? "Loading conditions" : conditionStatus === "partial" ? "Partial forecast" : conditionStatus === "unavailable" ? "Weather unavailable" : null;

  return <div className="analysis-workspace" role="region" aria-label="Route analysis">
    <header className="analysis-workspace-heading">
      <div><p className="section-kicker">Route analysis</p><h2 title={route.name}>{route.name}</h2></div>
      {noteworthyStatus && <span className={`analysis-status analysis-status-${conditionStatus}`}>{noteworthyStatus}</span>}
    </header>

    <div className="analysis-left-column">
      <section className="analysis-spatial-viewport" aria-label="Future route spatial view">
        <div>
          <p className="section-kicker">Route view</p>
          <strong>2D / 3D route view</strong>
          <span>Spatial route exploration will occupy this area in a later milestone.</span>
        </div>
      </section>

      <section className="analysis-chart-stack" aria-label="Route profile analysis">
        <div className="analysis-mode-controls analysis-workspace-modes" role="group" aria-label="Analysis mode">
          {ANALYSIS_MODES.map(({ mode, label }) => <button key={mode} type="button" title={`${label} analysis`} aria-label={`${label} analysis`} aria-pressed={conditionMode === mode} onClick={() => onConditionModeChange(mode)}>{label}</button>)}
        </div>
        <div className="analysis-profile-card">
          <RouteProfile wide route={route} schedule={schedule} conditions={conditions} conditionMode={conditionMode} focusedIndex={activeIndex} pinnedIndex={pinnedIndex ?? 0} onFocusChange={onPreviewChange} onPreviewChange={onPreviewChange} onPinnedChange={onPinnedChange} />
        </div>
        {legend && <div className="route-condition-legend analysis-workspace-legend"><span>{legend.label} · {legend.units}</span><i style={{ background: legend.gradient }} /><div>{legend.values.map((value) => <em key={value}>{value}</em>)}</div></div>}
      </section>
    </div>

    <section className="analysis-detail-card">
      {focusedSample ? <ForecastDetails sample={focusedSample} derived={conditions?.derived ?? null} /> : <div className="route-point-pending"><p className="section-kicker">Journey point details</p><h3>Route start · 0.0 km</h3><p>{conditionStatus === "loading" ? "Preparing route-start conditions…" : "Route-start weather is unavailable for the current forecast, while terrain and timing remain selected."}</p></div>}
    </section>
  </div>;
}
