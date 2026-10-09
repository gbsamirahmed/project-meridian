# Native-grid window experiment — frozen design

9 October 2026. Exact clean public main/origin/main start
`ebbc0cc305dc9f31c443d8c2a916da12722bddf4`; fetched divergence 0/0.

## Scope and closure before extraction

Use one Python/GeoTIFF experimental window binding over the accepted v1 projection.
Retain all three exact publication pins, all qualified documents, full vectors,
four Swiss tiles and WorldCover bytes. No expected answers as builder input.

The reader first transforms/densifies the query and clips to the EPSG:2056 core.
Thus every subsequent vertex/point lies in that closed core, even for partially
intersecting or much larger valid input areas. Bound the whole core, not samples.
For the pinned PROJ 9.5.1 inverse-somerc/Bessel/three-translation/WGS84 pipeline,
a coarse analytic enclosure gives Bessel longitude [7.73452,7.78734] degrees and
translation longitude change below 0.01228 degrees. Reserve [7.71,7.81] degrees,
with ±1 m input guard and a further native-column guard. The selected window is
**[column 2554,row 0,width 366,height 3600]**. All source rows are retained: latitude
extrema and the unproved 94 × 66 window are deliberately not needed for closure.
The complete derivation, monotonic inequalities and floating-point limitations
are recorded in the study report and executable closure checks before building.

Scientific source metadata stays full-grid: 3600 × 3600, original affine/CRS,
SHA256, nodata, datum, time, rights and provenance. Stored crop metadata has a
separate byte seal, local affine and shape, and an explicit source-grid offset.
Queries still calculate original row/column and original conservative descriptors.
An out-of-window pixel request is an integrity failure, never valid empty evidence.
The closure is specific to the checked operation/toolchain, not arbitrary PROJ builds.

## Verification and lifecycle boundary

Use an explicitly versioned `atlas-native-window-experiment/v1` outer manifest,
containing the unchanged original v1 manifest and a separate physical-member closure.
A captured window view translates absolute reads; it does not change scientific
query logic or fabricate full-source bytes. Reuse accepted generation verification
against original seals/metadata only after the new stored binding is verified.
Checksums prove integrity relative to an expected identity, not trusted origin or
independent proof of source derivation. Builder verifies the full accepted baseline
and compares every extracted float32 bit; originals remain untouched.

Introduce only narrow overridable snapshot/manifest/reader factories where necessary
in the existing spike Reader/Store/shared owner. Default v1 behaviour stays tested;
no new installer or scientific engine. Ready selection remains separate from exact
scientific generation. Captured owned raster bytes preserve post-open consistency.

## Acceptance and bounded measurements

Run the unchanged 60 complete outcomes over three pins, plus deterministic novel
core points, source-cell boundaries, CRS variants, seams/corners, partially clipped
areas and independent original-index/pixel anchors. Verify bad/missing/corrupt crops,
wrong offsets/headers/schema/pins, post-open mutation, injected staging/commit failure,
last-ready preservation and fresh-process restart. Regenerate twice byte-identically.
Measure original versus variant serially, one and three shared views, three fresh
processes each, 15 warm queries/type/pin. No storage-cold or Android claims.

New variant is expected below 85 MB (estimate), one candidate + one ready + one stage
below 255 MB; run destructive tests serially in owned scratch. Inherited 512 MiB
scratch/store and 768 MiB desktop memory bounds remain. Never change original packages,
canonical data, accepted reports, contracts or frozen fixtures. No mobile/renderer,
private access, acquisition, UI, Weather, final format or production deployment.
Stop at one measured result or precise closure/technical blocker; do not pursue
minimal latitude cropping or general raster compression in this task.


## Completed result and schema

**DEMONSTRATED**, within the checked desktop/profile boundary.
[Study report](../../../../docs/research/atlas-native-grid-window.md) records the
whole-core analytic enclosure, exact indices/qualifications, finite-test limitations,
rights and measurements; [results](results.json) retains path-free trial diagnostics.
The experimental package is 77,412,208 bytes, DSM 3,306,806 bytes. It is neither a
rendering product nor the original source artefact. The 94 × 66 descriptor remains
an accepted query result, not the stored-window proof.

`atlas-native-window-experiment/v1` contains `profile`, the unchanged logical
`sourceProjection` manifest, exact `pins`, physical `files` seals, `window` and
`projectionIdentity`. The window binds `sourceIdentity`, `sourceMember`, `sourceSeal`,
`sourceNative` (full original grid), `sourceWindow` (absolute column,row,width,height),
`storedMember`, `storedNative` (local grid), `pixelSha256`, `pixelEncoding`,
`processing` (storage method/modification notice/terms) and `closure`.
Pixel identity is little-endian IEEE754 float32, row-major, with no numeric conversion.
File identity is independently SHA256 of the TIFF bytes. All original rights and
qualification documents remain scientific records; the later storage change is
recorded separately. Metadata/manifests are bounded and exact member closure is verified.

The source crop does not claim full-source byte availability; only the original seal
and grid identity remain. Native point reads translate columns by 2554; areas use the
original source-affine support/window semantics. Requests outside the stored strip
fail integrity checks. Changed PROJ operation/version requires a new closure review.
The expected identity must come from a trusted channel; a self-consistent manifest
is not publisher authentication. No general power-loss or Android guarantees.

## Reproducible commands

Existing accepted v1 projection and the existing GIS Python environment are required;
no installation is prescribed. Two NEW output paths, stores and logs must be outside
Git and authoritative data. Frozen-fixture replay requires only the committed v1
fixtures; reference replay additionally needs the unchanged authority config, worlds
and twelve retained inputs identified in the fixture manifest. Replace placeholders.

```powershell
$studyPython = 'EXISTING_GIS_PYTHON'
$baseline = 'EXISTING_VERIFIED_V1_PROJECTION'
$window = 'NEW_OWNED_EXTERNAL_WINDOW_OUTPUT'
$reproduced = 'SECOND_NEW_OWNED_EXTERNAL_OUTPUT'
$config = 'EXISTING_LOCAL_AUTHORITY_CONFIG_JSON'
$store = 'NEW_OWNED_EXTERNAL_STORE'
$identity = 'ec6308b7c195af38190eebd4239fcfbe32b416308e2404b80777c598538363f9'
$generation = '5d364e9947040f705699416e9094d8ad59463b5b2c2fcae2e3efdf79a7410289'
& $studyPython -B scripts/atlas/portable-spike/native-window/closure.py
& $studyPython -B scripts/atlas/portable-spike/native-window/build.py --source $baseline --output $window
& $studyPython -B scripts/atlas/portable-spike/native-window/build.py --source $baseline --output $reproduced
# Compare every member byte hash, including manifest, in both generated directories.
$env:ATLAS_SPIKE_PROJECTION = $baseline
$env:ATLAS_WINDOW_PROJECTION = $window
& $studyPython -B -m unittest discover -s scripts/atlas/portable-spike/native-window -p 'test_*.py' -v
foreach ($trial in @(1,2,3)) {
  & $studyPython -B scripts/atlas/portable-spike/native-window/isolation.py --projection $window --baseline $baseline --config $config --fixtures fixtures/atlas-read/v1
  & $studyPython -B scripts/atlas/portable-spike/reduction/isolation.py --projection $baseline --config $config --fixtures fixtures/atlas-read/v1
}
# Serial fresh processes; three repeats per representation/count, 15 warm queries/type/pin.
foreach ($count in @(1,3)) {
  foreach ($trial in @(1,2,3)) {
    & $studyPython -B scripts/atlas/portable-spike/native-window/measure.py --projection $baseline --mode baseline --readers $count
    & $studyPython -B scripts/atlas/portable-spike/native-window/measure.py --projection $window --mode window --readers $count
  }
}
& $studyPython -B scripts/atlas/portable-spike/native-window/lifecycle.py --baseline $baseline --projection $window
& $studyPython -B scripts/atlas/portable-spike/native-window/local.py init --store $store
& $studyPython -B scripts/atlas/portable-spike/native-window/local.py install --store $store --projection $window --identity $identity
& $studyPython -B scripts/atlas/portable-spike/native-window/local.py query --store $store --identity $identity --generation $generation --query '{"region":"riffelhorn","families":["dsm"],"point":[2624500,1091500],"crs":"EPSG:2056"}'
# Explicit deletion clears selected state; no silent fallback.
& $studyPython -B scripts/atlas/portable-spike/native-window/local.py delete --store $store --identity $identity
```

Library boundary (experiment directory on the driver's import path):

```python
from window import WindowShared, WindowStore

with WindowShared.from_store(WindowStore(store_path), exact_storage_identity) as owner:
    with owner.pin(exact_scientific_generation) as view:
        result = view.outcome(query)
# Or WindowShared(projection_path, exact_storage_identity).
```

Inherited `Reader.manifest` denotes the unchanged scientific v1 binding;
`snapshot.storage_manifest` denotes the actual experimental storage manifest.
Do not confuse their identities. Each view closes before owner close. The test
suite injects faults only into owned copies, never the supplied original directories.
Stored geometry, GDAL snapshots, source datums/times and all exact query semantics
are retained. No second authority or fixture-request result table.

Executed proportional regressions use the unchanged commands:

```powershell
& $studyPython -B -m unittest discover -s scripts/atlas/portable-spike -p 'test_*.py' -v
& $studyPython -B -m unittest discover -s scripts/atlas/portable-spike/reduction -p 'test_*.py' -v
& $studyPython -B scripts/atlas/riffelhorn-retrieval/test_query.py
node --test scripts/atlas/read-conformance/test-fixtures.mjs
node --test runtime/atlas/test-runtime.mjs runtime/atlas/test-lifecycle.mjs runtime/atlas/test-registration.mjs runtime/atlas/test-retrieval.mjs
node scripts/atlas/read-conformance/run.mjs --config $config
npm.cmd run lint
node node_modules/typescript/bin/tsc -b --pretty false
node node_modules/vite/bin/vite.js build --config EXISTING_EXTERNAL_APP_ONLY_CONFIG
```

The app-only config excludes Weather processing/public-data copying. No full Weather
build, phone tests, rights clearance or production deployment is claimed. Exactly one
next task is defined in the report; it is **NOT BEGUN**.
