import assert from "node:assert/strict";
import test from "node:test";
import { createServer } from "vite";

const server = await createServer({
  appType: "custom",
  logLevel: "silent",
  server: { middlewareMode: true },
});
const geometry = await server.ssrLoadModule("/src/services/routeGeometry.ts");
const terrain = await server.ssrLoadModule("/src/services/routeTerrain.ts");
const journey = await server.ssrLoadModule("/src/services/journeyModel.ts");

test.after(async () => server.close());

function point(latitude, longitude) {
  return {
    textContent: null,
    getAttribute(name) {
      return name === "lat" ? String(latitude) : name === "lon" ? String(longitude) : null;
    },
    getElementsByTagNameNS() {
      return [];
    },
  };
}

function collection(children) {
  return {
    textContent: null,
    getAttribute() {
      return null;
    },
    getElementsByTagNameNS(_namespace, name) {
      return children[name] ?? [];
    },
  };
}

function gpxDocument({ name = "Test ridge", segments = [], routes = [], invalid = false }) {
  return {
    querySelector(selector) {
      return invalid && selector === "parsererror" ? collection({}) : null;
    },
    getElementsByTagNameNS(_namespace, localName) {
      if (localName === "name") {
        return [{ ...collection({}), textContent: name }];
      }
      if (localName === "trkseg") {
        return segments.map((points) => collection({ trkpt: points }));
      }
      if (localName === "rte") {
        return routes.map((points) => collection({ rtept: points }));
      }
      return [];
    },
  };
}

function imported(coordinates) {
  return {
    id: "route-test",
    name: "Synthetic route",
    coordinates,
    sourcePointCount: coordinates.length,
    sourceSegmentCount: 1,
  };
}

function flatTerrainRoute(distanceM = 4000, elevationM = 200) {
  const source = imported([
    { latitude: 55, longitude: -4 },
    { latitude: 55 + distanceM / 111195, longitude: -4 },
  ]);
  const resampled = geometry.resampleRouteGeometry(source, 100);
  return terrain.buildTerrainRoute(
    resampled,
    resampled.coordinates.map(() => elevationM)
  );
}

const basePlan = {
  mode: "profile",
  departureTime: "2026-09-01T08:00:00.000Z",
  targetDurationMinutes: 180,
  targetFinishTime: "2026-09-01T12:00:00.000Z",
};

test("GPX parsing selects and joins contiguous track segments", () => {
  const document = gpxDocument({
    segments: [
      [point(55, -4), point(55.001, -4)],
      [point(55.001, -4), point(55.002, -4)],
    ],
  });
  const route = geometry.parseGpxDocument(document, "Fallback");
  assert.equal(route.name, "Test ridge");
  assert.equal(route.coordinates.length, 3);
  assert.equal(route.sourceSegmentCount, 2);
  assert.throws(
    () => geometry.parseGpxDocument(gpxDocument({ invalid: true })),
    /not valid GPX/
  );
});

test("GPX route points are accepted when no track is present", () => {
  const route = geometry.parseGpxDocument(
    gpxDocument({ routes: [[point(51, 0), point(51.01, 0.01)]] })
  );
  assert.equal(route.coordinates.length, 2);
});

test("route resampling uses controlled distance and handles the antimeridian", () => {
  const route = geometry.resampleRouteGeometry(
    imported([
      { latitude: 0, longitude: 179.99 },
      { latitude: 0, longitude: -179.99 },
    ]),
    40
  );
  assert.ok(route.coordinates.length > 40);
  assert.ok(route.totalDistanceM > 2000 && route.totalDistanceM < 2300);
  assert.equal(route.cumulativeDistancesM[0], 0);
  assert.equal(route.cumulativeDistancesM.at(-1), route.totalDistanceM);
  assert.ok(route.coordinates.some((sample) => Math.abs(sample.longitude) > 179.99));
  const bounds = geometry.getRouteBounds(route.coordinates);
  assert.ok(bounds.east - bounds.west < 1);
  const display = geometry.unwrapRouteCoordinates(route.coordinates);
  assert.ok(
    display.slice(1).every(
      (point, index) => Math.abs(point.longitude - display[index].longitude) < 1
    )
  );
});

test("short and degenerate routes are rejected", () => {
  assert.throws(
    () => geometry.resampleRouteGeometry(imported([{ latitude: 1, longitude: 1 }])),
    /at least two/
  );
  assert.throws(
    () =>
      geometry.resampleRouteGeometry(
        imported([
          { latitude: 1, longitude: 1 },
          { latitude: 1, longitude: 1.000001 },
        ])
      ),
    /too short/
  );
});

test("elevation smoothing suppresses small noise but retains sustained ascent", () => {
  const noisy = Array.from({ length: 30 }, (_, index) => 100 + (index % 2));
  const noisyTotals = terrain.calculateAscentDescent(terrain.smoothElevations(noisy));
  assert.ok(noisyTotals.totalAscentM < 3);
  const climb = Array.from({ length: 31 }, (_, index) => 100 + index * 2);
  const climbTotals = terrain.calculateAscentDescent(terrain.smoothElevations(climb));
  assert.ok(climbTotals.totalAscentM >= 50);
  assert.equal(climbTotals.totalDescentM, 0);
});

test("gradient smoothing produces stable sustained slopes", () => {
  const distances = Array.from({ length: 21 }, (_, index) => index * 40);
  const elevations = distances.map((distance) => 100 + distance * 0.1);
  const gradients = terrain.calculateSmoothedGradients(elevations, distances);
  assert.ok(gradients.slice(3, -3).every((value) => Math.abs(value - 0.1) < 1e-9));
});

test("Tobler walking response distinguishes flat, slight descent, ascent and steep descent", () => {
  const profile = journey.DEFAULT_JOURNEY_PROFILE;
  const flat = journey.toblerWalkingSpeedKmh(0, profile);
  const slightDownhill = journey.toblerWalkingSpeedKmh(-0.05, profile);
  const ascent = journey.toblerWalkingSpeedKmh(0.15, profile);
  const steepDownhill = journey.toblerWalkingSpeedKmh(-0.35, profile);
  assert.ok(slightDownhill > flat);
  assert.ok(flat > ascent);
  assert.ok(flat > steepDownhill);
});

test("journey schedule separates movement and breaks and propagates arrivals", () => {
  const route = flatTerrainRoute();
  const profile = { ...journey.DEFAULT_JOURNEY_PROFILE, plannedBreakMinutes: 30 };
  const schedule = journey.buildJourneySchedule(route, profile, basePlan);
  assert.equal(schedule.stoppedMinutes, 30);
  assert.ok(schedule.totalMinutes > schedule.movingMinutes);
  assert.equal(schedule.samples[0].elapsedMinutes, 0);
  assert.equal(schedule.samples.at(-1).arrivalTime, schedule.expectedFinishTime);
  assert.equal(schedule.samples.at(-1).stoppedElapsedMinutes, 30);
  assert.ok(schedule.likelyMinimumMinutes < schedule.totalMinutes);
  assert.ok(schedule.likelyMaximumMinutes > schedule.totalMinutes);
});

test("target duration scales terrain-aware segment timing instead of distributing uniform speed", () => {
  const route = flatTerrainRoute(6000);
  route.samples.forEach((sample, index) => {
    sample.gradient = index < route.samples.length / 2 ? 0.12 : -0.05;
  });
  const profile = { ...journey.DEFAULT_JOURNEY_PROFILE, plannedBreakMinutes: 20 };
  const baseline = journey.buildJourneySchedule(route, profile, basePlan);
  const target = journey.buildJourneySchedule(route, profile, {
    ...basePlan,
    mode: "target-duration",
    targetDurationMinutes: baseline.totalMinutes * 0.85,
  });
  const baselineFirstHalf = baseline.samples[Math.floor(route.samples.length / 2)].movingElapsedMinutes;
  const targetFirstHalf = target.samples[Math.floor(route.samples.length / 2)].movingElapsedMinutes;
  assert.ok(target.movementScale > 1);
  assert.ok(
    Math.abs(
      baselineFirstHalf / baseline.movingMinutes -
        targetFirstHalf / target.movingMinutes
    ) < 1e-9
  );
  assert.equal(target.targetComparison, "faster-than-baseline");
});

test("finish constraints and degenerate targets are handled explicitly", () => {
  const route = flatTerrainRoute();
  const profile = journey.DEFAULT_JOURNEY_PROFILE;
  const finishTarget = journey.buildJourneySchedule(route, profile, {
    ...basePlan,
    mode: "target-finish",
    targetFinishTime: "2026-09-01T10:00:00.000Z",
  });
  assert.equal(finishTarget.expectedFinishTime, "2026-09-01T10:00:00.000Z");
  assert.throws(
    () =>
      journey.buildJourneySchedule(route, profile, {
        ...basePlan,
        mode: "target-duration",
        targetDurationMinutes: 20,
      }),
    /leave time for movement/
  );
});
