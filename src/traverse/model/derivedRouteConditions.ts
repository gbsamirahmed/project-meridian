import type { RouteConditionSample, ScalarRouteCondition } from "../types/routeConditions";
import type { DerivedConditionSample, DerivedRouteConditions, DerivedUnavailable, FreezingContext, RouteConditionEvent, VisibilityContext } from "../types/derivedRouteConditions";

/** Display/debounce policy, not risk bands or probabilistic forecast uncertainty.
 * See docs/derived-route-conditions.md for sources, measured evidence and limitations. */
export const DERIVED_THRESHOLDS = Object.freeze({
  nearFreezingM: 100,
  separatedFreezingLevelsM: 100,
  calmMs: 1852 / 3600, // Beaufort calm: below one knot
  lightMs: 3 * 1852 / 3600, // light air; don't emphasise route orientation
  componentDominanceMs: 1852 / 3600,
  veryPoorVisibilityM: 1000,
  poorVisibilityM: 2 * 1852,
  moderateVisibilityM: 5 * 1852,
});
const MISSING: DerivedUnavailable = { state: "unavailable", reason: "missing-input" };
const INCOMPATIBLE: DerivedUnavailable = { state: "unavailable", reason: "incompatible-reference" };
const EVIDENCE = ["temperature", "freezingLevel", "highestFreezingLevel", "wind", "gust", "visibility", "cloud", "cloudCeiling"] as const;

/** Spherical geopotential -> geometric height approximation, relative to mean sea level.
 * Does not claim to reconcile every source datum in the Terrarium composite. */
export function geopotentialToAltitudeM(heightGpm: number): number {
  const radiusM = 6_371_000;
  return Number.isFinite(heightGpm) && Math.abs(heightGpm) <= 30_000
    ? radiusM * heightGpm / (radiusM - heightGpm) : NaN;
}
function validScalar(value: ScalarRouteCondition): boolean {
  return value?.state === "available" && Number.isFinite(value.value);
}
function sameForecast(a: ScalarRouteCondition, b: ScalarRouteCondition): boolean {
  return a.state === "available" && b.state === "available" &&
    a.provenance.runTime === b.provenance.runTime && a.provenance.validTime === b.provenance.validTime;
}
export function deriveFreezing(sample: RouteConditionSample): FreezingContext {
  const { freezingLevel: level, highestFreezingLevel: highest } = sample.weather;
  const elevation = sample.terrain.elevationM;
  if (level?.state !== "available" || !validScalar(level) || elevation === null || !Number.isFinite(elevation)) return MISSING;
  if (level.units !== "gpm" || level.provenance.verticalReference !== "mean-sea-level") return INCOMPATIBLE;
  const altitudeM = geopotentialToAltitudeM(level.value);
  if (!Number.isFinite(altitudeM)) return INCOMPATIBLE;
  const highestAltitudeM = highest?.state === "available" && validScalar(highest) && highest.units === "gpm" &&
    highest.provenance.verticalReference === "mean-sea-level" && sameForecast(level, highest)
    ? geopotentialToAltitudeM(highest.value) : null;
  const comparableHighest = highestAltitudeM !== null && Number.isFinite(highestAltitudeM) ? highestAltitudeM : null;
  const difference = comparableHighest === null ? null : comparableHighest - altitudeM;
  const separationM = elevation - altitudeM;
  return {
    state: "available", altitudeM, highestAltitudeM: comparableHighest, separationM, levelDifferenceM: difference,
    position: separationM < -DERIVED_THRESHOLDS.nearFreezingM ? "below" : separationM > DERIVED_THRESHOLDS.nearFreezingM ? "above" : "near",
    structure: difference === null ? "unknown" : difference > DERIVED_THRESHOLDS.separatedFreezingLevelsM ? "multiple-levels-indicated" :
      difference < -DERIVED_THRESHOLDS.separatedFreezingLevelsM ? "inconsistent-levels" : "no-separated-levels-indicated",
  };
}
export function visibilityCategory(valueM: number): VisibilityContext {
  if (!Number.isFinite(valueM) || valueM < 0) return MISSING;
  return { state: "available", category: valueM < DERIVED_THRESHOLDS.veryPoorVisibilityM ? "very-poor" :
    valueM < DERIVED_THRESHOLDS.poorVisibilityM ? "poor" : valueM < DERIVED_THRESHOLDS.moderateVisibilityM ? "moderate" : "good" };
}
export function deriveConditionSample(sample: RouteConditionSample): DerivedConditionSample {
  const { wind, gust, visibility, cloudCeiling } = sample.weather;
  let orientation: Extract<DerivedConditionSample["wind"], { state: "available" }>["orientation"] = "unknown";
  const windAvailable = wind.state === "available" && Number.isFinite(wind.speedMs);
  if (windAvailable) {
    if (wind.speedMs < DERIVED_THRESHOLDS.calmMs) orientation = "calm";
    else if (wind.speedMs < DERIVED_THRESHOLDS.lightMs) orientation = "light";
    else if (wind.relative) {
      const { alongRouteMs: along, crossRouteMs: cross } = wind.relative;
      const difference = Math.abs(along) - Math.abs(cross);
      orientation = Math.abs(difference) < DERIVED_THRESHOLDS.componentDominanceMs ? "mixed" : difference > 0 ?
        along < 0 ? "headwind" : "tailwind" : cross > 0 ? "crosswind-left" : "crosswind-right";
    }
  }
  const gustAvailable = gust?.state === "available" && validScalar(gust) && gust.units === "m/s" && gust.value >= 0;
  const comparableGust = gustAvailable && windAvailable && gust.provenance.runTime === wind.provenance.runTime && gust.provenance.validTime === wind.provenance.validTime;
  return {
    routeSampleIndex: sample.routeSampleIndex, evidenceFields: EVIDENCE,
    freezing: deriveFreezing(sample),
    wind: windAvailable ? { state: "available", orientation } : MISSING,
    gust: gustAvailable ? { state: "available", excessMs: comparableGust ? gust.value - wind.speedMs : null } : MISSING,
    visibilityCloud: {
      visibility: visibility?.state === "available" && visibility.units === "m" ? visibilityCategory(visibility.value) : MISSING,
      ceiling: cloudCeiling?.state !== "available" || !validScalar(cloudCeiling) ? MISSING :
        cloudCeiling.units !== "gpm" || cloudCeiling.provenance.verticalReference !== "model-surface" ? INCOMPATIBLE :
          Math.abs(cloudCeiling.value - 20000) <= 1 ? MISSING :
            { state: "available", reference: "model-surface", interpretation: "raw-only" },
    },
  };
}

/** Schmitt trigger: must leave both sides of the 200 m-wide near band before
 * emitting another crossing. Missing/ambiguous structure resets continuity.
 * A time-step change is a legitimate route × time change, not interpolated weather. */
export function freezingCrossings(raw: RouteConditionSample[], derived: DerivedConditionSample[]): RouteConditionEvent[] {
  const events: RouteConditionEvent[] = [];
  let side: -1 | 1 | null = null;
  let previous: number | null = null;
  let bracket: [number, number] | null = null;
  for (let i = 0; i < derived.length; i++) {
    const current = derived[i].freezing;
    if (current.state !== "available" || current.structure !== "no-separated-levels-indicated") {
      side = null; previous = null; bracket = null; continue;
    }
    if (previous !== null && side !== null) {
      const before = derived[previous].freezing as Extract<FreezingContext, { state: "available" }>;
      if (side * current.separationM < 0 && side * before.separationM >= 0) bracket = before.separationM === 0 ? [previous, previous] : [previous, i];
      if (side * current.separationM > 0) bracket = null;
    }
    const nextSide = current.position === "below" ? -1 : current.position === "above" ? 1 : null;
    if (side !== null && nextSide !== null && side !== nextSide && bracket) {
      const [from, to] = bracket;
      const a = raw[from], b = raw[to];
      events.push({ kind: "freezing-crossing", direction: nextSide === 1 ? "above" : "below",
        fromSampleIndex: a.routeSampleIndex, toSampleIndex: b.routeSampleIndex, confirmedAtSampleIndex: raw[i].routeSampleIndex,
        approximateDistanceM: (a.cumulativeDistanceM + b.cumulativeDistanceM) / 2,
        approximateArrivalTime: new Date((Date.parse(a.journey.expectedArrivalTime) + Date.parse(b.journey.expectedArrivalTime)) / 2).toISOString(),
      });
      bracket = null;
    }
    if (nextSide !== null) side = nextSide;
    previous = i;
  }
  return events;
}
export function buildDerivedRouteConditions(routeId: string, raw: RouteConditionSample[]): DerivedRouteConditions {
  const samples = raw.map(deriveConditionSample);
  const events = freezingCrossings(raw, samples);
  let visibilityStart: number | null = null;
  for (let i = 0; i <= samples.length; i++) {
    const visibility = samples[i]?.visibilityCloud.visibility;
    const poor = visibility?.state === "available" && (visibility.category === "poor" || visibility.category === "very-poor");
    if (poor && visibilityStart === null) visibilityStart = i;
    if (!poor && visibilityStart !== null) {
      events.push({ kind: "poor-visibility-section", fromSampleIndex: raw[visibilityStart].routeSampleIndex,
        toSampleIndex: raw[i - 1].routeSampleIndex, boundary: "observed-samples" });
      visibilityStart = null;
    }
  }
  for (const kind of ["peak-gust", "strongest-crosswind", "strongest-headwind", "minimum-visibility"] as const) {
    let best: { index: number; value: number } | null = null;
    raw.forEach((sample, index) => {
      const weather = sample.weather;
      const value = kind === "peak-gust" ? samples[index].gust.state === "available" && weather.gust.state === "available" ? weather.gust.value : null :
        kind === "minimum-visibility" ? samples[index].visibilityCloud.visibility.state === "available" && weather.visibility.state === "available" ? weather.visibility.value : null :
          weather.wind.state === "available" && weather.wind.relative ? kind === "strongest-crosswind" ? weather.wind.relative.crosswindMs : weather.wind.relative.headwindMs : null;
      if (value !== null && Number.isFinite(value) && (best === null || (kind === "minimum-visibility" ? value < best.value : value > best.value))) best = { index, value };
    });
    if (best !== null) {
      const selected = best as { index: number; value: number };
      events.push({ kind, fromSampleIndex: raw[selected.index].routeSampleIndex, toSampleIndex: raw[selected.index].routeSampleIndex,
        value: selected.value, units: kind === "minimum-visibility" ? "m" : "m/s" });
    }
  }
  const coverage = (predicate: (s: DerivedConditionSample) => boolean) => ({ availableSamples: samples.filter(predicate).length, totalSamples: samples.length });
  return { version: 1, routeId, samples, events,
    coverage: { freezing: coverage(s => s.freezing.state === "available"), wind: coverage(s => s.wind.state === "available"), gust: coverage(s => s.gust.state === "available"),
      visibility: coverage(s => s.visibilityCloud.visibility.state === "available"), ceiling: coverage(s => s.visibilityCloud.ceiling.state === "available") },
    summary: { aboveFreezingSamples: samples.filter(s => s.freezing.state === "available" && s.freezing.position === "above").length,
      multipleLevelSamples: samples.filter(s => s.freezing.state === "available" && (s.freezing.structure === "multiple-levels-indicated" || s.freezing.structure === "inconsistent-levels")).length,
      freezingCrossings: events.filter(e => e.kind === "freezing-crossing").length },
  };
}

/** Keeps forecast gaps and sample alignment. Profile clipping is a presentation choice. */
export function freezingProfileSeries(raw: RouteConditionSample[], derived: DerivedRouteConditions) {
  return raw.map((sample, index) => {
    const context = derived.samples[index];
    return { routeSampleIndex: sample.routeSampleIndex, distanceM: sample.cumulativeDistanceM,
      altitudeM: context?.routeSampleIndex === sample.routeSampleIndex && context.freezing.state === "available" ? context.freezing.altitudeM : null };
  });
}
