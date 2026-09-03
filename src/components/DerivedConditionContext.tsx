import type { RouteConditionSample } from "../types/routeConditions";
import type { DerivedConditionSample } from "../types/derivedRouteConditions";
import { freezingContextLabel, freezingStructureLabel, visibilityContextLabel, windContextLabel } from "../services/derivedConditionFormatting";
import { gustLabel, visibilityLabel } from "../services/atmosphericFormatting";

/** Interpretation references the aligned raw sample; raw values/details remain below. */
export default function DerivedConditionContext({ raw, context }: { raw: RouteConditionSample; context: DerivedConditionSample }) {
  const ambiguity = freezingStructureLabel(context.freezing);
  return <div className="derived-condition-context">
    <div><span>Wind / gust context</span><strong>{windContextLabel(context.wind)}</strong>
      <small>{raw.weather.wind.state === "available" ? `Sustained ${gustLabel(raw.weather.wind.speedMs)}` : "Sustained unavailable"}
        {raw.weather.gust.state === "available" ? ` · gusts ${gustLabel(raw.weather.gust.value)}` : " · gust unavailable"}</small>
    </div>
    <div><span>Visibility / cloud context</span><strong>{visibilityContextLabel(context.visibilityCloud.visibility)}
      {raw.weather.visibility.state === "available" ? ` · ${visibilityLabel(raw.weather.visibility.value)}` : ""}</strong>
      <small>Cloud ceiling remains above the model surface; no route/cloud intersection inferred.</small>
    </div>
    <div><span>Freezing context</span><strong>{freezingContextLabel(context.freezing)}</strong>
      {ambiguity && <small>{ambiguity}</small>}
      <small>Approximate sea-level comparison, not an ice forecast.</small>
    </div>
  </div>;
}
