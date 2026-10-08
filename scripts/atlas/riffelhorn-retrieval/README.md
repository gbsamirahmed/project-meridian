# Standalone Riffelhorn qualified retrieval

Run from project-meridian using the existing public-data GIS environment:

```powershell
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/riffelhorn-retrieval/query.py --query '{"point":[2625000, 1092000]}'
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/riffelhorn-retrieval/query.py --query '{"feature":"glaciers:683","associated":true}'
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/riffelhorn-retrieval/query.py --query '{"time":{"role":"evidence-epoch","start":2016,"end":2016}}'
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/riffelhorn-retrieval/test_query.py
```

`--mode scan|grouped|selective` changes candidate selection only. `--matrix`
returns semantic hashes for the frozen 29 real queries. Full verification of the
accepted preparation runs once at session startup, without writing it.

Allowed query fields: point OR area, crs (2056/4326/CRS84), source-scoped feature,
associated (actual parentGlacier relation), families, representation, product
(exact prepared selector), time (evidence-epoch/product-reference year range OR
explicit unknown). Unsupported fields/CRS/time precision fail. No source ranking.

Point pixels use the native affine half-open grid convention. Area vectors require
positive-area intersection; source geometries remain intact. Height areas return
native-window candidate descriptors, without a bulk sample array or aggregation.
WorldCover areas count native centres in the exact transformed query polygon;
counts are not physical fractions. Core applicability is separate from full
source support. Unknown time never matches every requested year.

Record identity and source/native qualifiers remain in answers. Geometry is
referenced by its immutable prepared asset/hash/selector. These are standalone
answers, not a published Atlas generation. All indexing is ephemeral: family
lists, an identity/parent dictionary and one 38-feature STRtree. Startup hydrates
all prepared metadata; warm selector savings do not imply selective physical disk
reads. Existing data/dependencies only; no API/database or persistent index.

`measure.py` runs the frozen comparison. `validate.py` records relevant regression
coverage/protection. Payload/window byte counters are logical decoded bytes, not
physical compressed-file traffic. Source bytes are assumed under unchanged local
custody between startup verification and queries; this is not a production trust
policy. See the durable report and frozen plan for limits and the next task.
