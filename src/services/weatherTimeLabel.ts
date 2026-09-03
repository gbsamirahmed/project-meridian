import type { RouteConditionProvenance } from "../types/routeConditions";

function localFormatter(timeZone?: string): Intl.DateTimeFormat {
  return new Intl.DateTimeFormat("en-GB", {
    weekday: "short", hour: "2-digit", minute: "2-digit",
    timeZoneName: "short", ...(timeZone ? { timeZone } : {}),
  });
}

export function accumulationIntervalLabel(
  step: { accumulationStart?: string; accumulationEnd?: string },
  timeZone?: string
): string {
  if (!step.accumulationStart || !step.accumulationEnd) return "Interval unavailable";
  return `Interval ${localFormatter(timeZone).formatRange(
    new Date(step.accumulationStart), new Date(step.accumulationEnd)
  )}`;
}

export function routeConditionTimeLabel(
  provenance: RouteConditionProvenance,
  timeZone?: string
): string {
  if (provenance.timeSemantics === "interval-total") {
    return accumulationIntervalLabel(provenance, timeZone);
  }
  const offset = provenance.temporalOffsetMinutes;
  const offsetLabel = Math.abs(offset) < 0.5
    ? "exact forecast time"
    : `${Math.round(Math.abs(offset))} min ${offset > 0 ? "after" : "before"} arrival`;
  return `Valid ${localFormatter(timeZone).format(new Date(provenance.validTime))} · ${offsetLabel}`;
}
