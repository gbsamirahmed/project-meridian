# Personal activity research tooling

This directory contains reusable offline ingestion and evidence-analysis code. It must be run against a private export outside the Meridian repository.

Install the sole third-party dependency:

```powershell
py -m pip install -r scripts/activity_research/requirements.txt
```

Run a representative sample before a full archive pass:

```powershell
py scripts/activity_research/analyze_strava_export.py --export-root <private-export> --output-root <private-output> --mode sample
py scripts/activity_research/analyze_strava_export.py --export-root <private-export> --output-root <private-output> --mode full
```

The source export is opened read-only. Generated JSON and Markdown intentionally omit raw coordinate sequences, but remain private because activity identifiers, dates, devices and aggregate movement history can still be sensitive. Always keep output outside Git.

Evidence thresholds are explicit constants in `models.py`. They distinguish plausible progression, stationary recording, explicit timer pauses, timestamp gaps, anomalous GPS movement and uncertain segments without treating Strava labels as ground truth.

Stationary evidence requires both no more than 3 m displacement and no more than 0.35 m/s. Slow but genuine progression remains movement evidence.
