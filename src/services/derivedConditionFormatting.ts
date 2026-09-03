import type { DerivedRouteConditions, FreezingContext, FreezingCrossingEvent, VisibilityContext, WindContext } from "../types/derivedRouteConditions";

export function freezingContextLabel(context: FreezingContext): string {
  if (context.state === "unavailable") return "Freezing context unavailable";
  const comparison = context.position === "near" ? "Near forecast 0°C level" :
    `~${Math.round(Math.abs(context.separationM) / 50) * 50} m ${context.position} forecast 0°C level`;
  return comparison;
}
export function freezingStructureLabel(context: FreezingContext): string | null {
  if (context.state === "unavailable") return null;
  if (context.structure === "multiple-levels-indicated") return "Multiple freezing levels indicated; comparison is to the lower diagnostic.";
  if (context.structure === "inconsistent-levels") return "Freezing diagnostics disagree; no simple boundary interpretation.";
  if (context.structure === "unknown") return "Highest-level comparison unavailable; structure uncertain.";
  return null;
}
export function windContextLabel(context: WindContext): string {
  if (context.state === "unavailable") return "Wind context unavailable";
  return { calm: "Calm sustained wind", light: "Light sustained wind", mixed: "Mixed along-route / crosswind",
    headwind: "Headwind-dominant", tailwind: "Tailwind-dominant", "crosswind-left": "Crosswind from left",
    "crosswind-right": "Crosswind from right", unknown: "Route orientation unavailable" }[context.orientation];
}
export function visibilityContextLabel(context: VisibilityContext): string {
  return context.state === "unavailable" ? "Model visibility unavailable" :
    `${{ "very-poor": "Very poor", poor: "Poor", moderate: "Moderate", good: "Good" }[context.category]} model visibility`;
}
export function crossingLabel(event: FreezingCrossingEvent): string {
  const roundedTime = new Date(Math.round(Date.parse(event.approximateArrivalTime) / 300000) * 300000);
  const time = new Intl.DateTimeFormat(undefined, { weekday: "short", hour: "2-digit", minute: "2-digit" }).format(roundedTime);
  return `Changes to ${event.direction} forecast 0°C level around ${(Math.round(event.approximateDistanceM / 500) / 2).toFixed(1)} km · ~${time}`;
}
export function freezingSummaryLabel(derived: DerivedRouteConditions): string {
  const { availableSamples, totalSamples } = derived.coverage.freezing;
  if (!availableSamples) return "Freezing context unavailable";
  const position = derived.summary.aboveFreezingSamples ? "Some available samples above forecast 0°C level" : "No available samples more than 100 m above forecast 0°C level";
  return `${position} · ${availableSamples}/${totalSamples} scheduled samples assessed${derived.summary.multipleLevelSamples ? " · multiple/ambiguous levels present" : ""}`;
}
