# Bounded offline imagery review

Default mode uses existing SWISSIMAGE and contour delivery products, without new
processing, credentials, external imagery requests or private application changes.

From the public repository with its existing dependencies:

```powershell
$env:MERIDIAN_DATA_ROOT = 'C:\Users\gbsam\Documents\Projects\meridian-data'
node scripts/atlas/imagery-review/serve.mjs
```

Open **http://127.0.0.1:5182/**. Compare Orthophoto, Contours and the optional
18% Swiss visual hillshade at Overview/z14 and Close terrain/z18. Drag/pinch/scroll
normally. Heights are retained LN02 contour-line values, not image-derived elevations.
This is a separate experiment, not Meridian's current Mapterhorn map or a new
satellite basemap. No geographical labels/path overlay is supplied.

Exact metadata hashes and per-request asset size/hash checks reject changed evidence.
Only inventoried PNG/MVT files and the retained shaded PNG are served. The local
server session stops after120 attempts or before exceeding40,000,000 payload bytes.
These are local experimental limits, not provider quotas. Restart for a deliberately
separate offline review if needed; it cannot reset any external-provider allowance.
No original RGB/DEM, unencoded fields, keys or arbitrary directory files are served.

```powershell
node --test scripts/atlas/imagery-review/test_*.mjs
node node_modules/eslint/bin/eslint.js --config scripts/atlas/imagery-review/eslint.config.mjs scripts/atlas/imagery-review/
$env:MERIDIAN_BROWSER_OUTPUT = 'C:\Users\gbsam\Documents\Codex\imagery-review-output'
node scripts/atlas/imagery-review/check_browser.mjs
```

Run the browser check on a fresh local server session. Existing installed Chromium
uses SwiftShader; the test blocks all non-loopback requests, captures Swiss-only
frames outside Git, checks flat rendering, controls, panning and reference-mobile
layout. It is not an Android or hardware-GPU benchmark. The reference tests execute
the unchanged public satellite module with synthetic fetch/map responses; no account
requests are made. The non-allowlisted URL case documents an existing limitation,
not a new external request or an assertion of a complete security audit.

The standard root build materialises the unrelated external weather publication.
For this documentation/standalone experiment, use existing root TypeScript/lint
checks and an isolated Vite build with `configFile:false`, `publicDir:false`,
`envDir:false` and an external `build.outDir`; no Weather publication is rebuilt.

See [the imagery review](../../../docs/atlas/satellite-imagery-foundations-review.md)
for current provider terms, pricing and the limits of these observations.

## Separately approved live comparison

The completed13 October trial used one document for five locations, with no global
image exports. Its permission does not authorise future trials. Only after renewed
owner approval of the account/quota and scope, stop this owned server and run:

```powershell
node scripts/atlas/imagery-review/serve.mjs --approved-maptiler
```

Open `http://127.0.0.1:5182/live.html` **once**. The explicit mode loads only the
existing ignored `VITE_MAPTILER_KEY`, which is client-visible; never commit it or
build a keyed distribution. Default/offline mode and an isolated build use an empty
key. No provider proxy, persistent imagery cache or tile archive is created.

Use the five location buttons and3 m/0.5 m per CSS pixel controls. Riffelhorn can
switch to the retained Swiss image at the identical camera; other locations cannot.
MapLibre pitch is zero; this harness has no terrain geometry, geographical labels
or numerical elevation interpretation. Source credits and official MapTiler logo
remain visible. Stop requests explicitly after review; close without reloading.

One metadata request and100 imagery attempts share30 MB of metered body allowance,
two concurrent requests and550 ms minimum start spacing. Per-response reservations
and a29 MB early stop are deliberately conservative. Unexpected/oversized responses,
redirects, refusals and exhausted limits stop without retries. Received chunks and
protocol overhead differ from declared/retained payload counts. The one-document
server permit prevents accidental reload-reset; restarting it does not renew the
owner's approval or cap abuse of a copied key. Tests use synthetic responses only.
The fixed official logo resource is separate from imagery/TileJSON counters.

No MapTiler screenshot files are exported by this utility or the offline browser
check. That check visits only the Swiss entry and blocks non-loopback requests.
Build both entries with an empty `__MAPTILER_KEY__` definition; put compiled output
outside Git. Do not run the offline check in an authorised live tab or replace a
MapTiler basemap with exported screenshots.
