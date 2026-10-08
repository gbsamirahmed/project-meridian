# Retained regional expansion assessment

Assessment-only; no fixture is built. Frozen decision criteria: plan.json.

Run from repository root with the existing public-data GIS environment:

```powershell
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/regional-expansion/inventory.py --check
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/regional-expansion/validate.py
```

The inventory reads named public Atlas records/manifests, stats listed files, checks selected current hashes/headers, and selects existing GLAMOS records in memory. No acquisition, source write, region preparation or private scan. Without --check it writes only the compact repository inventory; with --check it compares reconstruction without modifying it. Current hashing, current availability and prior provider/verification records are distinct.

The fixture JSON is a declarative handoff, not an Atlas component/publication or implemented preparation. Twelve existing input references remain in meridian-data. No payloads/dependencies/infrastructure are added. The durable report defines scientific/rights qualifications and the next proof’s stop boundary.
