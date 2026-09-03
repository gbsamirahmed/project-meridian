import ForecastDetails from "./ForecastDetails";
import RouteProfile from "./RouteProfile";
import { ROUTE_CONDITION_LEGENDS } from "../services/routeConditionStyle";
import type { JourneySchedule, TerrainRoute } from "../types/route";
import type { RouteConditionMode, RouteConditions, RouteConditionStatus } from "../types/routeConditions";

interface RouteAnalysisProps {
  route: TerrainRoute;
  schedule: JourneySchedule | null;
  conditions: RouteConditions | null;
  conditionStatus: RouteConditionStatus;
  conditionMode: RouteConditionMode;
  focusedIndex: number | null;
  onFocusChange: (index: number | null) => void;
  onConditionModeChange: (mode: RouteConditionMode) => void;
  onClose: () => void;
}

export default function RouteAnalysis({ route, schedule, conditions, conditionStatus, conditionMode, focusedIndex, onFocusChange, onConditionModeChange, onClose }: RouteAnalysisProps) {
  const legend = conditionMode === "none" ? null : ROUTE_CONDITION_LEGENDS[conditionMode];
  const focusedSample = focusedIndex === null ? null : conditions?.samples[Math.max(0, Math.min(conditions.samples.length - 1, focusedIndex))] ?? null;
  return (
    <section className="route-analysis desktop-surface" aria-label="Route analysis">
      <div className="route-analysis-toolbar">
        <div><p className="section-kicker">Route analysis</p><h2>{route.name}</h2></div>
        <label className="analysis-colour-control"><span>Route colour</span><select value={conditionMode} onChange={(event) => onConditionModeChange(event.target.value as RouteConditionMode)}><option value="none">Normal</option><option value="temperature">Temperature</option><option value="precipitation">Precipitation</option><option value="wind">Wind</option><option value="gradient">Gradient</option></select></label>
        <span className={`analysis-status analysis-status-${conditionStatus}`}>{conditionStatus === "loading" ? "Loading conditions" : conditionStatus === "partial" ? "Partial forecast coverage" : conditionStatus === "unavailable" ? "Weather unavailable" : conditionStatus === "ready" ? "Arrival weather ready" : "Terrain ready"}</span>
        <button type="button" className="surface-close-button" aria-label="Hide route analysis" onClick={onClose}>×</button>
      </div>
      <div className="route-analysis-content">
        <div className="route-profile-region">
          <RouteProfile route={route} schedule={schedule} conditions={conditions} conditionMode={conditionMode} focusedIndex={focusedIndex} onFocusChange={onFocusChange} wide />
          {legend && <div className="route-condition-legend analysis-legend"><span>{legend.label} · {legend.units}</span><i style={{ background: legend.gradient }} /><div>{legend.values.map((value) => <em key={value}>{value}</em>)}</div></div>}
        </div>
        <aside className="route-point-region">
          {focusedSample ? <ForecastDetails sample={focusedSample} derived={conditions?.derived ?? null} /> : <div className="route-point-empty"><p className="section-kicker">Journey point details</p><h3>Select the profile or route</h3><p>Move across the profile or choose a point on the map to inspect terrain and expected-arrival conditions.</p></div>}
        </aside>
      </div>
    </section>
  );
}
