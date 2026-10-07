# Tryfan pilot S3

Bounded retained slope → planar-area ratio integration. The [report](../../../docs/research/tryfan-pilot-s3.md) and [plan](../../../docs/research/tryfan-regional-pilot-plan.md) govern it. No HTTP/client or live applicability update.

```powershell
# Initialize once from a published S1 seed; refuses an already initialized G0.
node pilots/atlas/tryfan/lifecycle-cli.mjs initialize
node pilots/atlas/tryfan/lifecycle-cli.mjs inspect
node pilots/atlas/tryfan/lifecycle-cli.mjs assess
node pilots/atlas/tryfan/lifecycle-cli.mjs replay
node pilots/atlas/tryfan/lifecycle-cli.mjs query --request '{"property":"place-evidence","place":{"crs":"EPSG:27700","point":[266405,359387]}}'
node --test pilots/atlas/tryfan/tests/lifecycle.test.mjs
node pilots/atlas/tryfan/measure_s3.mjs --check
../meridian-data/earth-lab/.venv/Scripts/python.exe pilots/atlas/tryfan/validate_s3.py
```

`--store`, `--generation` (read commands) and `--data-root` are explicit options. The local state remains in `meridian-data/experiments/atlas/tryfan-regional-pilot-v1/`. Source files remain immutable. `methods().recompute` / `openUnderstanding().recomputeFixture` calculate the finite retained regional fixture without publishing it; S3 generation validation rejects regional update publication. Neither command nor API starts a scheduler/server.

Scientific claim IDs/revisions use the original method's canonicalization. Outer generations use S1 canonical UTF8 JSON. Operational timing and locator maps remain outside identity. `world.mjs` composes S2 and S3 with one pinned generation, fixed questions and separate evidence contexts. No source winner, physical appearance recovery or current-state claim.

Next: **Tryfan pilot generation-pinned serving and isolated consumer - S4 only**, not begun.
