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

Run the bounded terrain/personal-calibration experiment only after creating the full private ingestion output:

```powershell
py scripts/activity_research/run_personal_calibration.py --export-root <private-export> --ingestion-root <private-ingestion-output> --output-root <new-private-experiment-output>
```

The experiment selects complete activities from recorded behaviour rather than catalogue labels, reconstructs movement from timestamps, caches only the required Terrarium tiles under the private output, compares a small declared set of terrain-processing variants, and validates a transparent slope response using whole-activity folds. It never updates Meridian's production journey constants.

Generate a blind, frozen annotation catalogue for independent human review with explicit paths outside the repository:

```powershell
py scripts/activity_research/generate_activity_context.py --export-root <private-export> --research-root <private-research-root> --repo-root <meridian-repository> --fallback-cache <optional-private-dem-cache>
```

The context tool preserves the source catalogue, never passes activity names or descriptions into inference, and leaves every `human_*` field blank. It refuses to place private sources, outputs, or its DEM cache inside the Git worktree and refuses to overwrite an existing frozen `activity-context.csv`.
