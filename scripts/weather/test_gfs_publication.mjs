import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import {
  createGfsPublicationMiddleware,
  materializeGfsPublication,
  readGfsPublication,
  resolveGfsPublicationRoot,
  resolveGfsRequestPath,
} from "./gfs_publication.mjs";

const FIELDS = {
  precipitation: "manifest.json",
  cloud_cover: "cloud-cover/manifest.json",
  wind_10m: "wind-10m/manifest.json",
  temperature_2m: "temperature-2m/manifest.json",
  pressure_msl: "pressure-msl/manifest.json",
  gust_surface: "gust-surface/manifest.json",
  visibility_surface: "visibility-surface/manifest.json",
  freezing_level: "freezing-level/manifest.json",
  highest_freezing_level: "highest-freezing-level/manifest.json",
  cloud_ceiling: "cloud-ceiling/manifest.json",
};

function fixture() {
  const parent = path.join(os.tmpdir(), `meridian-gfs-publication-${process.pid}-${Date.now()}-${Math.random()}`);
  const repositoryRoot = path.join(parent, "project-meridian");
  const dataRoot = path.join(parent, "meridian-data");
  const root = path.join(dataRoot, "derived", "weather", "gfs");
  const runName = "20260907T18Z";
  mkdirSync(repositoryRoot, { recursive: true });
  const fields = {};
  for (const [field, relativeManifest] of Object.entries(FIELDS)) {
    const manifest = `${runName}/${relativeManifest}`;
    const target = path.join(root, ...manifest.split("/"));
    mkdirSync(path.dirname(target), { recursive: true });
    writeFileSync(target, JSON.stringify({ field }));
    fields[field] = { timestepCount: 24, manifest };
  }
  writeFileSync(path.join(root, "latest.json"), JSON.stringify({ schemaVersion: 2, fields }));
  mkdirSync(path.join(root, "20260907T12Z"));
  writeFileSync(path.join(root, "phase-4e-validation.json"), "not published");
  return { parent, repositoryRoot, dataRoot, root, runName };
}

test("resolves the external authoritative publication with sibling and environment roots", (context) => {
  const item = fixture();
  context.after(() => rmSync(item.parent, { recursive: true, force: true }));
  assert.equal(resolveGfsPublicationRoot({
    repositoryRoot: item.repositoryRoot,
    environment: {},
  }), item.root);
  assert.equal(resolveGfsPublicationRoot({
    repositoryRoot: item.repositoryRoot,
    environment: { MERIDIAN_DATA_ROOT: item.dataRoot },
  }), item.root);
});

test("rejects roots inside the repository", (context) => {
  const item = fixture();
  context.after(() => rmSync(item.parent, { recursive: true, force: true }));
  assert.throws(() => resolveGfsPublicationRoot({
    repositoryRoot: item.repositoryRoot,
    environment: { MERIDIAN_DATA_ROOT: path.join(item.repositoryRoot, "data") },
  }), /outside the Git repository/);
});

test("publication serves only latest and the catalogue-selected immutable run", (context) => {
  const item = fixture();
  context.after(() => rmSync(item.parent, { recursive: true, force: true }));
  assert.equal(readGfsPublication(item.root).runName, item.runName);
  assert.equal(
    resolveGfsRequestPath("/weather/gfs/latest.json?checked=1", item.root),
    path.join(item.root, "latest.json"),
  );
  assert.equal(
    resolveGfsRequestPath(`/weather/gfs/${item.runName}/manifest.json`, item.root),
    path.join(item.root, item.runName, "manifest.json"),
  );
  assert.throws(
    () => resolveGfsRequestPath("/weather/gfs/20260907T12Z/manifest.json", item.root),
    /outside the catalogue-selected/,
  );
  assert.throws(
    () => resolveGfsRequestPath("/weather/gfs/%2e%2e/secret", item.root),
    /Unsafe|outside/,
  );
});

test("materialization excludes previous runs and external validation state", (context) => {
  const item = fixture();
  context.after(() => rmSync(item.parent, { recursive: true, force: true }));
  const target = path.join(item.parent, "publication-view");
  const result = materializeGfsPublication(target, { publicationRoot: item.root });
  assert.equal(result.runName, item.runName);
  assert.ok(existsSync(path.join(target, "latest.json")));
  assert.equal(JSON.parse(readFileSync(path.join(target, "latest.json"), "utf8")).schemaVersion, 2);
  assert.ok(existsSync(path.join(target, item.runName, "manifest.json")));
  assert.equal(existsSync(path.join(target, "20260907T12Z")), false);
  assert.equal(existsSync(path.join(target, "phase-4e-validation.json")), false);
  assert.throws(
    () => materializeGfsPublication(target, { publicationRoot: item.root }),
    /Refusing to overwrite/,
  );
});

for (const middlewareMode of [true, false]) {
  test(`${middlewareMode ? "middleware test" : "listening browser"} server shutdown does not materialize production Weather`, (context) => {
    const item = fixture();
    context.after(() => rmSync(item.parent, { recursive: true, force: true }));
    const output = path.join(item.parent, "dist");
    // Keep the fixture's root override inside a child process, isolated from other tests.
    const result = spawnSync(process.execPath, ["--input-type=module", "--eval", `
      import assert from "node:assert/strict";
      import { createServer } from "vite";
      const middlewareMode = process.argv[2] === "true";
      const server = await createServer({
        logLevel: "silent",
        server: { middlewareMode, host: "127.0.0.1", port: 0 },
        build: { outDir: process.argv[1] },
      });
      try {
        if (!middlewareMode) {
          await server.listen();
          const address = server.httpServer.address();
          const response = await fetch("http://127.0.0.1:" + address.port + "/weather/gfs/latest.json");
          assert.equal(response.status, 200);
          assert.equal(Object.keys((await response.json()).fields).length, 10);
        }
      } finally { await server.close(); }
    `, output, String(middlewareMode)], {
      cwd: fileURLToPath(new URL("../../", import.meta.url)),
      env: { ...process.env, MERIDIAN_DATA_ROOT: item.dataRoot },
      encoding: "utf8",
      windowsHide: true,
      timeout: 30_000,
    });
    assert.equal(result.status, 0, result.error?.message ?? result.stderr);
    assert.equal(existsSync(output), false, "Server shutdown must not produce build output");
  });
}

test("missing authoritative data fails the Weather request clearly without blocking other paths", (context) => {
  const item = fixture();
  context.after(() => rmSync(item.parent, { recursive: true, force: true }));
  const missingRoot = path.join(item.dataRoot, "derived", "weather", "missing-gfs");
  const middleware = createGfsPublicationMiddleware({ publicationRoot: missingRoot });
  let nextCalled = false;
  const unrelatedResponse = {};
  middleware({ url: "/" }, unrelatedResponse, () => { nextCalled = true; });
  assert.equal(nextCalled, true);

  let body = "";
  const response = {
    statusCode: 0,
    end(value) { body = value; },
    setHeader() {},
  };
  middleware({ url: "/weather/gfs/latest.json" }, response, () => {});
  assert.equal(response.statusCode, 503);
  assert.match(body, /^GFS publication unavailable:/);
});
