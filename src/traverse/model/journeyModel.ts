import type {
  JourneyPlan,
  JourneyProfile,
  JourneySchedule,
  JourneyScheduleSample,
  TargetPaceComparison,
  TerrainRoute,
} from "../types/route";

const PACE_MULTIPLIER = {
  relaxed: 0.82,
  normal: 1,
  fast: 1.18,
} as const;
const PARTY_MULTIPLIER = { solo: 1, group: 0.97 } as const;
const LOAD_MULTIPLIER = { light: 1, heavy: 0.9 } as const;
const MIN_SUPPORTED_TARGET_SCALE = 0.35;
const MAX_SUPPORTED_TARGET_SCALE = 2.5;

export const DEFAULT_JOURNEY_PROFILE: JourneyProfile = {
  activity: "hiking",
  pace: "normal",
  party: "solo",
  load: "light",
  plannedBreakMinutes: 30,
};

function isoAt(startMilliseconds: number, elapsedMinutes: number): string {
  return new Date(startMilliseconds + elapsedMinutes * 60000).toISOString();
}

export function toblerWalkingSpeedKmh(
  gradient: number,
  profile: JourneyProfile
): number {
  const slope = Math.max(-0.5, Math.min(0.5, gradient));
  const baseline = 6 * Math.exp(-3.5 * Math.abs(slope + 0.05));
  const calibrated =
    baseline *
    PACE_MULTIPLIER[profile.pace] *
    PARTY_MULTIPLIER[profile.party] *
    LOAD_MULTIPLIER[profile.load];
  return Math.max(0.8, Math.min(7, calibrated));
}

function targetTotalMinutes(plan: JourneyPlan, departureMs: number): number | null {
  if (plan.mode === "profile") return null;
  if (plan.mode === "target-duration") return plan.targetDurationMinutes;
  const finishMs = Date.parse(plan.targetFinishTime);
  if (!Number.isFinite(finishMs)) {
    throw new Error("Choose a valid target finish time.");
  }
  return (finishMs - departureMs) / 60000;
}

function compareScale(scale: number): TargetPaceComparison {
  if (scale < 0.9) return "slower-than-baseline";
  if (scale > 1.1) return "faster-than-baseline";
  return "close-to-baseline";
}

export function buildJourneySchedule(
  route: TerrainRoute,
  profile: JourneyProfile,
  plan: JourneyPlan
): JourneySchedule {
  if (route.samples.length < 2 || route.totalDistanceM < 10) {
    throw new Error("The route is too short for a journey estimate.");
  }
  if (route.elevationCoverage !== "complete") {
    throw new Error("Complete terrain elevation is required for journey timing.");
  }
  if (!Number.isFinite(profile.plannedBreakMinutes) || profile.plannedBreakMinutes < 0) {
    throw new Error("Planned break time must be zero or greater.");
  }
  const departureMs = Date.parse(plan.departureTime);
  if (!Number.isFinite(departureMs)) {
    throw new Error("Choose a valid departure time.");
  }
  const segmentBaselineMinutes: number[] = [];
  for (let index = 1; index < route.samples.length; index++) {
    const previous = route.samples[index - 1];
    const current = route.samples[index];
    const distanceM = current.cumulativeDistanceM - previous.cumulativeDistanceM;
    const gradient =
      previous.gradient === null || current.gradient === null
        ? null
        : (previous.gradient + current.gradient) / 2;
    if (gradient === null || distanceM <= 0) {
      throw new Error("The route contains incomplete terrain timing data.");
    }
    const speedKmh = toblerWalkingSpeedKmh(gradient, profile);
    segmentBaselineMinutes.push((distanceM / 1000 / speedKmh) * 60);
  }
  const baselineMovingMinutes = segmentBaselineMinutes.reduce(
    (sum, minutes) => sum + minutes,
    0
  );
  const requestedTotal = targetTotalMinutes(plan, departureMs);
  let movementScale = 1;
  if (requestedTotal !== null) {
    const requestedMoving = requestedTotal - profile.plannedBreakMinutes;
    if (!Number.isFinite(requestedMoving) || requestedMoving <= 1) {
      throw new Error("The target must leave time for movement after planned breaks.");
    }
    movementScale = baselineMovingMinutes / requestedMoving;
    if (
      movementScale < MIN_SUPPORTED_TARGET_SCALE ||
      movementScale > MAX_SUPPORTED_TARGET_SCALE
    ) {
      throw new Error("The target duration is outside this model's supported range.");
    }
  }
  const movingMinutes = baselineMovingMinutes / movementScale;
  const stoppedMinutes = profile.plannedBreakMinutes;
  const totalMinutes = movingMinutes + stoppedMinutes;
  const uncertaintyRate =
    0.12 +
    (profile.party === "group" ? 0.04 : 0) +
    (profile.load === "heavy" ? 0.04 : 0) +
    (Math.abs(movementScale - 1) > 0.25 ? 0.03 : 0);
  const finishSpreadMinutes = Math.max(
    10,
    movingMinutes * uncertaintyRate + stoppedMinutes * 0.25
  );
  let movingElapsed = 0;
  const samples: JourneyScheduleSample[] = route.samples.map((sample, index) => {
    if (index > 0) {
      movingElapsed += segmentBaselineMinutes[index - 1] / movementScale;
    }
    const progress = movingMinutes > 0 ? movingElapsed / movingMinutes : 0;
    const stoppedElapsed = stoppedMinutes * progress;
    const elapsed = movingElapsed + stoppedElapsed;
    const spread = finishSpreadMinutes * Math.sqrt(Math.max(0, progress));
    return {
      routeSampleIndex: sample.index,
      cumulativeDistanceM: sample.cumulativeDistanceM,
      movingElapsedMinutes: movingElapsed,
      stoppedElapsedMinutes: stoppedElapsed,
      elapsedMinutes: elapsed,
      arrivalTime: isoAt(departureMs, elapsed),
      earliestArrivalTime: isoAt(departureMs, Math.max(0, elapsed - spread)),
      latestArrivalTime: isoAt(departureMs, elapsed + spread),
    };
  });
  return {
    routeId: route.id,
    departureTime: plan.departureTime,
    expectedFinishTime: isoAt(departureMs, totalMinutes),
    movingMinutes,
    stoppedMinutes,
    totalMinutes,
    likelyMinimumMinutes: Math.max(0, totalMinutes - finishSpreadMinutes),
    likelyMaximumMinutes: totalMinutes + finishSpreadMinutes,
    movementScale,
    targetComparison: compareScale(movementScale),
    samples,
  };
}
