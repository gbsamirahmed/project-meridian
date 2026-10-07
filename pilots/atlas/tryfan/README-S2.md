# Retained Tryfan pilot — S2

Read-only qualified native evidence over a published S1 generation. [S2 report](../../../docs/research/tryfan-pilot-s2.md), [frozen matrix](query-matrix.json), [S1 tooling](README.md). S1 README/report remain historical; S2 is complete and S3 has not begun.

Requires existing Node/repository dependencies and the sibling retained geospatial Python environment. No new install/acquisition. From repository root:

```powershell
node pilots/atlas/tryfan/query-cli.mjs inspect
node pilots/atlas/tryfan/query-cli.mjs matrix
node pilots/atlas/tryfan/query-cli.mjs query --request '{"point":[266405,359387],"crs":"EPSG:27700","property":"coexisting-semantic"}'
node --test pilots/atlas/tryfan/tests/query.test.mjs
..\meridian-data\earth-lab\.venv\Scripts\python.exe pilots/atlas/tryfan/adapters/test_native.py
..\meridian-data\earth-lab\.venv\Scripts\python.exe pilots/atlas/tryfan/validate_s2.py
```

`query` takes one finite JSON request (see report). `--store`, `--generation`, `--data-root`, `--locators` reuse S1 selection/locator semantics. Every response exposes the pinned generation. No discovery/writer/HTTP/derivation commands. WorldCover/NRW are separate native evidence, not current universal cover. Appearance is dated metadata only. Current physical cover/appearance and unsupported properties do not fall back.

Library `openEvidence` returns `query`, developer metadata/semantics copies, generation, capabilities, metrics and `close`; close in `finally`. A finite Python worker reads only verified registered artifacts. Missing-family operational unavailable is separate from v1 scientific gaps; hash/reference/CRS/geometry failures are explicit. Point queries retain native cell/polygon support; support rectangles use BNG native-centre counts/intersections, not physical fractions.

`node pilots/atlas/tryfan/measure_s2.mjs` reproduces compact metrics/results from retained bytes. Timings/RSS are observations outside identity. Full matrix output is deterministically hashed and reproducible, not committed as duplicated imagery/geometry. All native sources and published S1 generations stay external/unchanged.

Next: **Tryfan pilot retained derivation and lifecycle integration - S3 only**, not begun. Production Atlas/Weather/Traverse unchanged; appearance unresolved/non-blocking and Swiss multiview parked.
