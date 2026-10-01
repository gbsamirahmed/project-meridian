import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { test } from "node:test";

const require = createRequire(import.meta.url);
const readJson = (url) => JSON.parse(readFileSync(url, "utf8"));

test("installed and locked MapLibre remain outside the attribution XSS range", () => {
  const manifest = readJson(new URL("../../package.json", import.meta.url));
  const lock = readJson(new URL("../../package-lock.json", import.meta.url));
  const installed = readJson(require.resolve("maplibre-gl/package.json"));
  const entries = Object.entries(lock.packages).filter(([name]) =>
    name.endsWith("node_modules/maplibre-gl")
  );
  assert.ok(entries.length > 0, "MapLibre must be present in the lockfile");
  assert.equal(installed.version, manifest.dependencies["maplibre-gl"]);
  assert.equal(lock.packages[""].dependencies["maplibre-gl"], installed.version);
  assert.equal(lock.packages["node_modules/maplibre-gl"].version, installed.version);
  for (const version of [installed.version, ...entries.map(([, entry]) => entry.version)]) {
    const match = /^(\d+)\.(\d+)\.(\d+)$/.exec(version);
    assert.ok(match, `Expected a stable MapLibre release: ${version}`);
    const [major, minor, patch] = match.slice(1).map(Number);
    assert.ok(
      major > 6 || (major === 6 && (minor > 4 || (minor === 4 && patch >= 1))),
      `GHSA-jrc7-96c5-q579 affects MapLibre ${version}; require >=6.4.1`
    );
  }
});
