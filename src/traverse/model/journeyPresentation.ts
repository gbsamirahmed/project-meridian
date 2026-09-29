import type { RouteConditionFieldCoverage, RouteConditions, RouteScalarKey } from "../types/routeConditions";

export function durationLabel(minutes: number): string {
  const rounded = Math.max(0, Math.round(minutes / 5) * 5);
  const hours = Math.floor(rounded / 60);
  const remainder = rounded % 60;
  return hours ? `${hours} h${remainder ? ` ${remainder} min` : ""}` : `${remainder} min`;
}

export function timeLabel(iso: string): string {
  return new Intl.DateTimeFormat(undefined, {
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
}

export function localInputValue(iso: string): string {
  const date = new Date(iso);
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 16);
}

export function isoFromLocal(value: string, fallback: string): string {
  const parsed = new Date(value);
  return Number.isFinite(parsed.getTime()) ? parsed.toISOString() : fallback;
}

export function coverageMessage(
  conditions: RouteConditions,
  key: RouteScalarKey | "wind",
  label: string
): string | null {
  const coverage: RouteConditionFieldCoverage = conditions.coverage[key];
  if (coverage.totalSamples > 0 && coverage.availableSamples === coverage.totalSamples) return null;
  if (coverage.availableSamples === 0) return `${label} is unavailable for this journey.`;

  let finalLeadingDistance = 0;
  let leading = true;
  let availableAfterGap = false;
  for (const sample of conditions.samples) {
    const available = sample.weather[key].state === "available";
    if (leading && available) finalLeadingDistance = sample.cumulativeDistanceM;
    if (!available) leading = false;
    else if (!leading) availableAfterGap = true;
  }
  if (!availableAfterGap && finalLeadingDistance > 0) {
    return `${label} is unavailable after approximately ${(finalLeadingDistance / 1000).toFixed(1)} km.`;
  }
  return `${label} is unavailable in part of the journey.`;
}

export function combinedCoverageMessages(conditions: RouteConditions): string[] {
  const messages = [
    coverageMessage(conditions, "temperature", "Temperature"),
    coverageMessage(conditions, "precipitation", "Rain"),
    coverageMessage(conditions, "gust", "Gusts"),
    coverageMessage(conditions, "visibility", "Visibility"),
  ].filter((message): message is string => Boolean(message));
  return Array.from(new Set(messages));
}
