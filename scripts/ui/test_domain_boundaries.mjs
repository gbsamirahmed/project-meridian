import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";
import test from "node:test";

const root = path.resolve(import.meta.dirname, "..", "..", "src");

function files(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const target = path.join(directory, entry.name);
    return entry.isDirectory() ? files(target) : [target];
  });
}

function imports(directory) {
  return files(path.join(root, directory))
    .filter((file) => statSync(file).isFile() && /\.(ts|tsx)$/.test(file))
    .flatMap((file) => {
      const text = readFileSync(file, "utf8");
      return [...text.matchAll(/(?:from\s+|import\s*)["']([^"']+)["']/g)]
        .map((match) => ({ file: path.relative(root, file), specifier: match[1] }));
    });
}

test("domain imports follow the frozen Phase 5 direction", () => {
  const atlas = imports("atlas");
  const weather = imports("weather");
  const traverse = imports("traverse");

  assert.deepEqual(
    atlas.filter(({ specifier }) => /(?:^|\/)weather(?:\/|$)|(?:^|\/)traverse(?:\/|$)/.test(specifier)),
    []
  );
  assert.deepEqual(
    weather.filter(({ specifier }) => /(?:^|\/)app(?:\/|$)|(?:^|\/)traverse(?:\/|$)/.test(specifier)),
    []
  );
  assert.deepEqual(
    traverse.filter(({ specifier }) =>
      /weather\/(?:data|map)\//.test(specifier) ||
      /globalWeather|numericTileCache|routeWeatherSampler/.test(specifier)
    ),
    []
  );
});

test("Weather has no Traverse schedule dependency", () => {
  for (const file of files(path.join(root, "weather"))) {
    if (!/\.(ts|tsx)$/.test(file)) continue;
    assert.doesNotMatch(readFileSync(file, "utf8"), /JourneySchedule/);
  }
});

test("shared remains absent unless a neutral owner is justified", () => {
  assert.equal(readdirSync(root).includes("shared"), false);
});