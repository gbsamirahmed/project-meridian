/** Opt-in real-asset smoke test. No generated data or local paths are fixtures.
 * MERIDIAN_WEATHER_URL points to a running dev server; MERIDIAN_TEST_PYTHON
 * points to an environment with Pillow. PNG decoding is not browser acceptance.
 */
import assert from "node:assert/strict";
import test from "node:test";
import { spawn } from "node:child_process";
import { createServer } from "vite";

test("served catalogue and PNGs sample through the real route/source/cache path", {
  skip: !process.env.MERIDIAN_WEATHER_URL || !process.env.MERIDIAN_TEST_PYTHON,
}, async () => {
  const server = await createServer({ appType: "custom", logLevel: "silent", server: { middlewareMode: true } });
  const weather = await server.ssrLoadModule("/src/weather/data/globalWeatherService.ts");
  const route = await server.ssrLoadModule("/src/traverse/model/routeConditions.ts");
  const sampler = await server.ssrLoadModule("/src/weather/data/routeWeatherSampler.ts");
  const cache = await server.ssrLoadModule("/src/weather/data/numericTileCache.ts");
  const originals = { window: globalThis.window, document: globalThis.document, createImageBitmap: globalThis.createImageBitmap, fetch: globalThis.fetch };
  const decodeFailures = [];
  const requestFailures = [];
  const urls = new Set(); let requests = 0, bytes = 0;
  globalThis.window = { location: { href: process.env.MERIDIAN_WEATHER_URL } };
  globalThis.fetch = async (...args) => {
    requests++; urls.add(String(args[0]));
    try {
      const response = await originals.fetch(...args);
      if (!response.ok) requestFailures.push(`${response.status}: ${args[0]}`);
      return response;
    } catch (error) { requestFailures.push(`${error.message} (${error.cause?.code ?? "unknown"}): ${args[0]}`); throw error; }
  };
  globalThis.createImageBitmap = async blob => {
    try {
      assert.match(blob.type, /image\/png/);
      const png = Buffer.from(await blob.arrayBuffer()); bytes += png.length;
      // Decode without blocking Node's HTTP event loop while other tiles arrive.
      const pixels = await new Promise((resolve, reject) => {
        const child = spawn(process.env.MERIDIAN_TEST_PYTHON, ["-c",
          "import sys,io,struct; from PIL import Image; im=Image.open(io.BytesIO(sys.stdin.buffer.read())).convert('RGBA'); sys.stdout.buffer.write(struct.pack('<II',*im.size)+im.tobytes())"], {
          stdio: ["pipe", "pipe", "pipe"], windowsHide: true,
        });
        const output = [], errors = [];
        const timeout = setTimeout(() => { child.kill(); reject(new Error("PNG test decoder exceeded 30 seconds")); }, 30_000);
        child.stdout.on("data", chunk => output.push(chunk));
        child.stderr.on("data", chunk => errors.push(chunk));
        child.on("error", error => { clearTimeout(timeout); reject(error); });
        child.on("close", code => {
          clearTimeout(timeout);
          if (code !== 0) reject(new Error(Buffer.concat(errors).toString()));
          else resolve(Buffer.concat(output));
        });
        child.stdin.on("error", reject);
        child.stdin.end(png);
      });
      assert.equal(pixels.readUInt32LE(0), 256);
      assert.equal(pixels.readUInt32LE(4), 256);
      return { data: new Uint8ClampedArray(pixels.subarray(8)), close() {} };
    } catch (error) { decodeFailures.push(error.message); throw error; }
  };
  globalThis.document = { createElement: () => {
    let image;
    return { getContext: () => ({ drawImage(value) { image = value; }, getImageData() { return { data: image.data }; } }) };
  } };
  try {
    const loaded = await weather.loadGlobalWeatherSources();
    assert.equal(Object.values(loaded.statuses).filter(s => s === "ready").length, 10);
    const s = loaded.sources;
    const sources = { temperature: s.temperature_2m, precipitation: s.precipitation, cloud: s.cloud_cover, wind: s.wind_10m, gust: s.gust_surface, visibility: s.visibility_surface, freezingLevel: s.freezing_level, highestFreezingLevel: s.highest_freezing_level, cloudCeiling: s.cloud_ceiling };
    const first = Date.parse(s.gust_surface.manifest.timesteps[0].validTime);
    const at = hours => new Date(first + hours * 3600000).toISOString();
    // Public, deliberately coarse coordinates; not imported personal GPX points.
    const places = [[-0.1, 51.5], [-3, 54.5], [179.9, 0], [-179.9, 0]];
    const terrain = { id: "smoke", totalDistanceM: 300, samples: places.map(([longitude, latitude], index) => ({ index, longitude, latitude, cumulativeDistanceM: index * 100, smoothedElevationM: 0, gradient: 0 })) };
    const schedule = times => ({ routeId: "smoke", samples: times.map((arrivalTime, index) => ({ routeSampleIndex: index, arrivalTime, earliestArrivalTime: arrivalTime, latestArrivalTime: arrivalTime, movingElapsedMinutes: 0, stoppedElapsedMinutes: 0, elapsedMinutes: 0 })) });
    const buildConditions = async journey => {
      const requests = terrain.samples.map((point, index) => ({
        coordinate: { longitude: point.longitude, latitude: point.latitude },
        requestedTime: journey.samples[index].arrivalTime,
      }));
      const samples = await sampler.sampleRouteWeather(requests, sources);
      return route.buildRouteConditions(terrain, journey, samples);
    };
    const conditions = await buildConditions(schedule([at(1), at(1), at(1), at(1)]));
    assert.deepEqual(requestFailures, [], "Publication requests must succeed");
    assert.deepEqual(decodeFailures, [], "PNG decoder must succeed");
    assert.equal(conditions.derived.coverage.freezing.availableSamples, 4);
    assert.equal(conditions.derived.coverage.visibility.availableSamples, 4);
    assert.equal(conditions.derived.coverage.gust.availableSamples, 4);
    assert.equal(conditions.derived.samples[0].freezing.position, "below");
    assert.equal(conditions.derived.samples[0].visibilityCloud.ceiling.reference, "model-surface");
    assert.equal(conditions.derived.samples[0].freezing.highestAltitudeM !== null, true);
    for (const key of ["temperature", "precipitation", "cloud", "wind", "gust", "visibility", "freezingLevel", "highestFreezingLevel"]) assert.equal(conditions.coverage[key].availableSamples, 4, key);
    const count = requests;
    await buildConditions(schedule([at(1), at(1), at(1), at(1)]));
    assert.equal(requests, count, "repeat route should reuse shared cache");
    const partial = await buildConditions(schedule([at(1), at(10), at(25), at(34)]));
    assert.equal(partial.derived.coverage.freezing.availableSamples, 2);
    assert.equal(partial.derived.coverage.gust.availableSamples, 2);
    assert.equal(partial.derived.samples[3].freezing.state, "unavailable");
    for (const key of ["gust", "visibility", "freezingLevel", "highestFreezingLevel"]) {
      assert.equal(partial.coverage[key].availableSamples, 2);
      assert.equal(partial.samples[3].weather[key].reason, "outside-forecast");
    }
    for (const [key, source] of Object.entries(sources).filter(([key]) => key !== "wind")) {
      const step = source.manifest.timesteps[1];
      const value = await cache.sampleScalarField(source, step, ...places[0]);
      const condition = conditions.samples[0].weather[key];
      if (value === null) assert.equal(condition.state, "unavailable");
      else assert.equal(condition.value, value, key);
    }
    const stats = cache.getNumericTileCacheStats();
    assert.equal(stats.pendingCount, 0);
    assert.ok(stats.bytes <= 64 * 1024 * 1024);
    console.log(JSON.stringify({ run: s.gust_surface.manifest.runTime, values: Object.fromEntries(Object.entries(conditions.samples[0].weather).map(([key, c]) => [key, c.state === "available" ? c.value ?? c.speedMs : c.reason])), requests, uniqueUrls: urls.size, pngBytes: bytes, cache: stats }));
  } finally { Object.assign(globalThis, originals); await server.close(); }
});
