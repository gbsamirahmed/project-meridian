# Atlas component-granularity experiment

Isolated metadata evidence at checkpoint `97c31c8`. This is not production Atlas storage.

The prospectively frozen [plan](plan.json) controls 148 query cases, 48 updates and
24 historical observations. The [report](../../../docs/research/atlas-component-granularity.md)
distinguishes synthetic unit supports from unchanged retained native qualifications.

From the repository root, use the existing earth-lab Python runtime:

```powershell
& '../meridian-data/earth-lab/.venv/Scripts/python.exe' scripts/atlas/component-granularity/run.py --check
& '../meridian-data/earth-lab/.venv/Scripts/python.exe' scripts/atlas/component-granularity/test_model.py
& '../meridian-data/earth-lab/.venv/Scripts/python.exe' scripts/atlas/component-granularity/validate.py
```

`run.py` constructs a new campaign only. It refuses existing campaign fixture paths.
Never remove/overwrite measured fixtures to rerun it: freeze a separate campaign/root
and retain its plan and source hashes. The current external state is
`C:/Users/gbsam/Documents/Codex/atlas-component-granularity-v1`; committed summaries
pin every raw observation and setup receipt. No accepted Tryfan store is rewritten.

`model.py` implements four fixed experimental organisations: whole leaf, spatially
ordered 64-record partitions, flat one-record memberships, and a key-ordered
64-record/fanout-16 authenticated internal tree. It preserves direct committed
publication eligibility and immutable content identity. It is a single sequential
writer, with no multiwriter or remote durability claim. Every request verifies the
selected metadata; publishing validates the complete descriptor/reference closure.
Tests deliberately corrupt/remove only owned throwaway fixtures.

Counters expose directories, pages, records, SHA verification, requested metadata
bytes and constructor reuse comparisons separately. Each request clears in-process
cache; OS caches are not flushed. The synthetic reader never reads payload bytes.
Native GIS queries, actual lifecycle computation and source hashes are verified by
the unchanged established regression commands.

`report.py` is post-measurement analysis: it adds explicit pin/manifest-size labels
from immutable receipts and renders the decisions/report. Its archive inventory
scans are reporting work outside all measured read paths. `plot.py` renders a
standalone SVG from the committed measurements. No index/cache/database product,
new scientific evidence, new physical method or runtime import is introduced.
