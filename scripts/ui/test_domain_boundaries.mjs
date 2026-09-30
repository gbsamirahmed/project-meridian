import assert from "node:assert/strict";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import ts from "typescript";

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
    atlas.filter(({ specifier }) => /(?:^|\/)app(?:\/|$)|(?:^|\/)weather(?:\/|$)|(?:^|\/)traverse(?:\/|$)/.test(specifier)),
    []
  );
  assert.deepEqual(
    weather.filter(({ specifier }) => /(?:^|\/)app(?:\/|$)|(?:^|\/)traverse(?:\/|$)/.test(specifier)),
    []
  );
  assert.deepEqual(
    traverse.filter(({ specifier }) =>
      /(?:^|\/)app(?:\/|$)|weather\/(?:data|map)\//.test(specifier) ||
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

// Include type-only edges: the two audited cycles were not runtime imports.
function sourceGraph() {
  const graph = new Map();
  for (const file of files(root).filter((file) => /\.(ts|tsx)$/.test(file))) {
    const references = ts.preProcessFile(readFileSync(file, "utf8"), true).importedFiles;
    const targets = references.filter(({ fileName }) => fileName.startsWith("."))
      .map(({ fileName }) => {
        if (/\.(css|svg)$/.test(fileName)) {
          const asset = path.resolve(path.dirname(file), fileName);
          assert.ok(existsSync(asset), `missing asset: ${asset}`);
          return asset;
        }
        const resolved = ts.resolveModuleName(fileName, file, {
          moduleResolution: ts.ModuleResolutionKind.Bundler,
          allowImportingTsExtensions: true,
        }, ts.sys).resolvedModule;
        assert.ok(resolved, `${path.relative(root, file)}: unresolved ${fileName}`);
        return resolved.resolvedFileName;
      }).filter((target) => /\.(ts|tsx)$/.test(target));
    graph.set(path.normalize(file), targets.map((target) => path.normalize(target)));
  }
  return graph;
}

test("active imports resolve and the audited Weather/Traverse type layers are acyclic", () => {
  const graph = sourceGraph();
  const complete = new Set();
  const stack = [];
  function visit(file) {
    const cycleStart = stack.indexOf(file);
    assert.equal(cycleStart, -1,
      `dependency cycle: ${[...stack.slice(cycleStart), file].map((p) => path.relative(root, p)).join(" -> ")}`);
    if (complete.has(file)) return;
    stack.push(file);
    for (const target of graph.get(file) ?? []) visit(target);
    stack.pop();
    complete.add(file);
  }
  // Guard the audited layering, without imposing a new global-acyclic policy.
  for (const file of [
    "weather/types/globalWeather.ts", "weather/data/atmosphericFields.ts",
    "weather/types/atmosphericFields.ts", "traverse/types/routeConditions.ts",
    "traverse/types/derivedRouteConditions.ts", "traverse/types/routeConditionBase.ts",
  ]) visit(path.join(root, file));
});

test("the frozen transitional files and old technical-kind directories are retired", () => {
  for (const obsolete of [
    "components", "services", "types", "config",
    "app/types/layer.ts", "app/config/layerVisuals.ts",
    "app/config/dataAttribution.ts", "app/map/mapLayerOrder.ts",
  ]) assert.equal(existsSync(path.join(root, obsolete)), false, obsolete);
});
