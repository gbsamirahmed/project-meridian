import assert from "node:assert/strict";
import test from "node:test";
import { createServer } from "vite";

const server = await createServer({
  appType: "custom",
  logLevel: "silent",
  server: { middlewareMode: true },
});
const model = await server.ssrLoadModule(
  "/src/services/temperatureContourModel.ts"
);

test.after(async () => {
  await server.close();
});

test("adaptive intervals use stable nice values", () => {
  assert.equal(model.chooseTemperatureContourInterval(2, 80), 10);
  assert.equal(model.chooseTemperatureContourInterval(5, 50), 5);
  assert.equal(model.chooseTemperatureContourInterval(8, 20), 2.5);
  assert.equal(model.chooseTemperatureContourInterval(10, 12), 2);
  assert.equal(model.chooseTemperatureContourInterval(13, 0.5), null);
});

test("one continuous contour crosses a synthetic tile boundary without duplicates", () => {
  const matrix = Array.from({ length: 7 }, () =>
    Array.from({ length: 9 }, (_, column) => column)
  );
  const bounds = { west: -4, south: -3, east: 4, north: 3 };
  const first = model.buildTemperatureContourData(matrix, bounds, 8);
  const second = model.buildTemperatureContourData(matrix, bounds, 8);
  assert.deepEqual(second, first);
  const fiveDegree = first.features.filter(
    (feature) => feature.properties.level === 5
  );
  assert.equal(fiveDegree.length, 1);
  assert.ok(fiveDegree[0].geometry.coordinates.length >= 6);
  assert.ok(
    fiveDegree[0].geometry.coordinates.every(
      ([longitude, latitude]) =>
        Number.isFinite(longitude) && Number.isFinite(latitude)
    )
  );
});

test("no-data cells are not contoured", () => {
  const matrix = Array.from({ length: 7 }, () =>
    Array.from({ length: 9 }, (_, column) => column)
  );
  matrix[3][5] = Number.NaN;
  const result = model.buildTemperatureContourData(
    matrix,
    { west: -4, south: -3, east: 4, north: 3 },
    8
  );
  assert.ok(
    result.features.every((feature) =>
      feature.geometry.coordinates.every(
        ([longitude, latitude]) =>
          Number.isFinite(longitude) && Number.isFinite(latitude)
      )
    )
  );
  assert.equal(
    result.features.some((feature) =>
      feature.geometry.coordinates.some(
        ([longitude, latitude]) => longitude === 1 && latitude === 0
      )
    ),
    false
  );
});
