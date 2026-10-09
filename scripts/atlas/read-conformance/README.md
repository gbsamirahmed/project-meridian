# Atlas read reference conformance

Frozen scope before fixture generation: 9 October 2026, public checkpoint
`984e7d2b8ebe3b3fe5a358ba7087af5a19d5f282`.

Use existing `AtlasContext.retrieve` and `scanEvidence`; do not implement scientific
predicates here. Reuse `riffelhorn-retrieval/matrix.json` (apart from its standalone
`associated` extension, tested as unsupported) and `runtime/atlas/retrieval-cases.mjs`
for accepted identities, scalar anchors and lineage. Select the registration-world
history entries 2 and 3 before/after the accepted controlled qualification revision,
and the first accepted multi-region generation for genuinely unknown knowledge time.
They are exact published pins, not fabricated observations or newly published worlds.

Acceptance: at least 25 fixed diverse requests, generated complete expected semantic
envelopes/errors from the authoritative full scan, indexed/full agreement, repeat
reference replay and a single-case command. Keep every scientific field and array
order; remove only the top-level operational `metrics` using the existing `semantic`
helper. Store shared documents once without changing their identities or contents.
No unavailable retained input is a skip or permission to generate substitute answers.
Stop on an authoritative/reference discrepancy; never modify scientific semantics.

No writes to canonical data/publications, SDKs, acquisition, endpoints, mobile reader,
UI, rendering, Weather or private repositories. Catalogue writes use an owned temporary
directory outside the repository and all authoritative roots, removed after contexts
close. Generation outputs must target a new external directory. Compact fixtures are
bounded to 2 MiB total; they contain metadata/answers, never source raster payloads.

## Contract and prerequisites

See the [read profile](../../../docs/atlas/portable-read-contract.md),
[manifest](../../../fixtures/atlas-read/v1/manifest.json) and
[results/limitations](../../../docs/research/atlas-portable-read.md).
Sixty fixed cases bind three exact committed generations. Source/preparation and
method/revision identities, native support/time, uncertainty, rights and full document
contents are compared; only top-level operational metrics are excluded. A successful
expected error is a passing rejection case, not a skipped scientific result.

Use Node 24.11+, installed repository dependencies and the existing GIS Python 3.12
environment documented by the runtime. The fixture manifest records exact generation
tool versions and all 12 retained Riffelhorn source identities. Full authoritative
opening also requires the accepted Tryfan closure in those multi-region worlds.
No SDK, phone, network service, acquisition or Python installation is needed.

Create an **uncommitted external** JSON config with explicit `dataRoot`, `python`,
`registrationWorld` and `legacyWorld` locators. Relative paths resolve against the
config file's parent. Do not put this file or physical user paths in the fixtures.
The following uses existing receipt locators, which must already be available:

```powershell
# Run from the public repository root. No install or source preparation.
$readData = (Resolve-Path ../meridian-data).Path
$readRegistration = Get-Content -Raw -Encoding utf8 docs/research/atlas-local-retrieval-baseline.json | ConvertFrom-Json
$readLegacy = Get-Content -Raw -Encoding utf8 docs/research/atlas-local-runtime-baseline.json | ConvertFrom-Json
$readConfig = Join-Path $env:TEMP 'meridian-atlas-read-config.json'
$readPaths = @{
  dataRoot = $readData
  python = Join-Path $readData 'earth-lab/.venv/Scripts/python.exe'
  registrationWorld = $readRegistration.selectedWorld
  legacyWorld = $readLegacy.publicationRoot
} | ConvertTo-Json
[IO.File]::WriteAllText($readConfig, $readPaths, [Text.UTF8Encoding]::new($false))
node scripts/atlas/read-conformance/run.mjs --config $readConfig
# One case is independently replayable; only its selected context is opened.
node scripts/atlas/read-conformance/run.mjs --config $readConfig --case native-tile-seam
node --test scripts/atlas/read-conformance/test-fixtures.mjs
```

On another retained installation, substitute explicit relocated public roots and the
GIS interpreter. Do not silently select different generations. Missing inputs or
reference-fingerprint/source mismatches abort with nonzero status, never a skip.

## Reference generation and inspection

```powershell
# NEW_EXTERNAL_DIRECTORY must not exist, and must be outside canonical roots/repository.
node scripts/atlas/read-conformance/generate.mjs --config $readConfig --output NEW_EXTERNAL_DIRECTORY
```

Generation invokes `scanEvidence` then checks `retrieve` for every request before
writing any fixture output. It writes the manifest last, has no automatic update
mode, and must not overwrite accepted expectations. A discrepancy stops generation;
review actual authority rather than changing semantics or hiding the failure.
Review all four emitted files before any authorised version change. Their compact
JSON only changes presentation; source response document hashes still use the accepted
canonical identity encoding. Regeneration on the recorded toolchain should reproduce
the four exact file hashes; different environments require explicit examination.

For inspection or another test adapter, `loadFixtures()` returns `cases`, `expected`,
`documents` and `manifest`; `unpackOutcome(expected[id], documents)` reconstructs the
complete semantic answer/error. No expected value is calculated by a second query engine.
The request's publication alias resolves through the manifest to an exact generation;
it is a fixture selector, not a physical data location or production transport.

`run.mjs` emits JSON lines per case and a final selected/passed/failed/skipped/error/
comparison summary. Both indexed and full-scan outputs must match the committed
expectation. A failed comparison identifies the method and first differing semantic
path; it does not dump source bodies or local paths. Missing/corrupt fixtures and
configuration/authority failures are blockers. Unsupported and invalid input share
some current runtime error codes; the `unsupportedRequest` scenario flag is test
metadata, not a new runtime capability/error taxonomy.

Catalogue writes use a new owned OS-temporary directory, outside canonical roots;
session closure removes it. Caller-requested generation outputs persist only in the
new explicitly chosen external directory. No catalogue or full source payload is
committed. Twelve focused tests need only the committed fixture files; the reference
runner additionally needs retained data/publications. Neither establishes portability,
mobile performance, offline completeness, renderer choice or cross-platform conformance.
