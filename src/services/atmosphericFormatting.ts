import type { RouteConditionFieldCoverage } from "../types/routeConditions";

export function gustLabel(metresPerSecond: number): string {
  return `~${Math.round(metresPerSecond * 3.6)} km/h`;
}

export function visibilityLabel(metres: number): string {
  if (metres < 1000) return `~${Math.round(metres / 10) * 10} m`;
  return `~${(metres / 1000).toFixed(metres < 10000 ? 1 : 0)} km`;
}

/** gpm retained internally; deliberately approximate user-facing height. */
export function atmosphericHeightLabel(geopotentialMetres: number): string {
  return `~${Math.round(geopotentialMetres / 50) * 50} m`;
}

export function fieldCoverageLabel(coverage: RouteConditionFieldCoverage): string {
  return coverage.availableSamples === coverage.totalSamples
    ? "All scheduled samples"
    : `${coverage.availableSamples}/${coverage.totalSamples} scheduled samples`;
}
