# Isolated Tryfan / Riffelhorn composition proof

Run from project-meridian with the existing Node and public-data GIS environment:

```powershell
node scripts/atlas/multi-region/prove.mjs
node --test scripts/atlas/multi-region/test-proof.mjs
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/multi-region/validate.py
```

`prove.mjs` creates a new isolated child under the frozen plan's Codex proof root,
seeds exact accepted Tryfan components, registers the pinned Riffelhorn preparation,
and publishes G1/G2/G3 with one administrative regional revision per transition.
It compares complete native envelopes with unhooked Tryfan and full-scan Riffelhorn
oracles, measures three warm repetitions, then replays in three fresh processes.
Large/source/prepared payloads remain external. No accepted store is written.

The two registration components preserve native support, identities, time, rights
and preparation lineage. Current publication plus the existing immutable membership
trie pins all seven component identities. Normal reads never walk predecessors.
Original pilot loading is confined to seeding and independent oracle comparison.
Full current verification remains mandatory at publication, including Riffelhorn
inside the existing writer lock. No trusted receipts, new verification policy or
production storage infrastructure is introduced.

`worker.mjs consumer <store> [generation]` is a finite JSON-line subprocess boundary,
not HTTP or a public API. It accepts `{ "requests": [{ "region": "riffelhorn",
"query": { "feature": "glaciers:683", "associated": true } }] }` on stdin and
returns one pinned qualified composite answer. Explicit Tryfan queries retain the
existing `openWorld` envelope; Riffelhorn queries retain the prepared retrieval
contract. Regions are disconnected. There is no source ranking or fusion.

The core/runtime extension is process-local: existing files and contracts stay
unchanged. The pilot generation validator remains Tryfan-specific; the composition
adapter validates the two registrations and exact original Tryfan science rather
than advertising a generalized production schema. Root replacement, immutable
component writes, bounded membership and dead-writer recovery use the existing core.

Measurements distinguish synchronous Node requested reads, Python logical hash
bytes and decoded raster windows from physical disk traffic. OS cache is not cleared.
Riffelhorn startup verifies/hydrates all metadata, and composite requests hydrate all
seven components; native selective candidates do not erase that overhead. Local
single-writer/process-crash semantics do not establish power-loss or cloud durability.

The durable report and structured next-task boundary are authoritative. The next
regional derivation proof is NOT BEGUN by these commands.
