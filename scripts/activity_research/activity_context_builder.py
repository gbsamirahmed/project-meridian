from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from activity_context import (
    ALLOWED_VALUES,
    INFERENCE_VERSION,
    INSERTED_COLUMNS,
    ContextGuess,
    RecordingFeatures,
    categorical_distribution,
    inference_methodology,
    infer_context,
    recording_features,
    terrain_features,
    unavailable_guess,
    unknown_terrain,
)
from parsers import parse_recording
from terrain_experiment import (
    TERRAIN_VARIANTS,
    MovementPoint,
    TerrariumTileCache,
    build_movement_chains,
    build_terrain_profile,
    resample_movement_chains,
)


MAX_DEM_TILES = 8_000
TERRAIN_VARIANT = TERRAIN_VARIANTS[0]
HUMAN_COLUMNS = tuple(column for column in INSERTED_COLUMNS if column.startswith("human_"))


@dataclass(slots=True)
class PreparedRecording:
    source_path: Path | None
    recording: RecordingFeatures | None
    points: list[MovementPoint]
    parse_error: str | None = None


@dataclass(slots=True, frozen=True)
class CatalogueLayout:
    description_index: int
    insertion_index: int
    activity_type_index: int
    filename_index: int


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_recording_fingerprint(activities_root: Path) -> dict[str, Any]:
    files = sorted(path for path in activities_root.rglob("*") if path.is_file())
    aggregate = hashlib.sha256()
    total_bytes = 0
    for path in files:
        relative = path.relative_to(activities_root).as_posix()
        size = path.stat().st_size
        total_bytes += size
        aggregate.update(relative.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(str(size).encode("ascii"))
        aggregate.update(b"\0")
        aggregate.update(bytes.fromhex(sha256_file(path)))
        aggregate.update(b"\n")
    return {
        "file_count": len(files),
        "total_bytes": total_bytes,
        "content_sha256": aggregate.hexdigest(),
    }


def read_catalogue(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        try:
            header = next(reader)
        except StopIteration as error:
            raise ValueError("activities.csv is empty") from error
        return header, list(reader)


def catalogue_layout(header: Sequence[str]) -> CatalogueLayout:
    normalized = [column.strip().casefold() for column in header]
    try:
        description = normalized.index("activity description")
        activity_type = normalized.index("activity type")
        filename = normalized.index("filename")
    except ValueError as error:
        raise ValueError("activities.csv is missing a required catalogue column") from error
    insertion = description + 1
    if insertion >= len(header) or normalized[insertion] != "elapsed time":
        raise ValueError(
            "Expected the first Elapsed Time column immediately after Activity Description"
        )
    return CatalogueLayout(description, insertion, activity_type, filename)


def _normalise_reference(value: str) -> str:
    return value.strip().replace("\\", "/").lstrip("./")


def resolve_recording(export_root: Path, reference: str) -> Path | None:
    normalized = _normalise_reference(reference)
    if not normalized:
        return None
    candidate = (export_root / normalized).resolve()
    activities_root = (export_root / "activities").resolve()
    if candidate != activities_root and activities_root not in candidate.parents:
        raise ValueError("Catalogue recording reference escapes activities/")
    return candidate if candidate.is_file() else None


def prepare_recording(path: Path | None) -> PreparedRecording:
    if path is None:
        return PreparedRecording(None, None, [], "Referenced recording is missing")
    try:
        activity = parse_recording(path)
        features = recording_features(activity)
        points = resample_movement_chains(
            build_movement_chains(activity), spacing_m=TERRAIN_VARIANT.spacing_m
        )
        return PreparedRecording(path, features, points)
    except Exception as error:  # one malformed private recording must not abort annotation
        return PreparedRecording(path, None, [], f"{type(error).__name__}: recording parse failed")


def _row_with_context(
    original: Sequence[str], insertion_index: int, guess: ContextGuess
) -> list[str]:
    values = guess.codex_values()
    inserted = [values[column] if column.startswith("codex_") else "" for column in INSERTED_COLUMNS]
    return list(original[:insertion_index]) + inserted + list(original[insertion_index:])


def _write_csv(path: Path, header: Sequence[str], rows: Sequence[Sequence[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\r\n")
        writer.writerow(header)
        writer.writerows(rows)
    temporary.replace(path)


def _write_json_atomic(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def _git_head(repo_root: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True
    ).strip()


def validate_output(
    original_header: Sequence[str],
    original_rows: Sequence[Sequence[str]],
    output_header: Sequence[str],
    output_rows: Sequence[Sequence[str]],
    layout: CatalogueLayout,
) -> None:
    expected_header = (
        list(original_header[: layout.insertion_index])
        + list(INSERTED_COLUMNS)
        + list(original_header[layout.insertion_index :])
    )
    if list(output_header) != expected_header:
        raise ValueError("Output columns do not match the required alternating layout")
    if len(output_rows) != len(original_rows):
        raise ValueError("Output row count differs from activities.csv")
    inserted_count = len(INSERTED_COLUMNS)
    codex_indices = {
        column: layout.insertion_index + INSERTED_COLUMNS.index(column)
        for column in INSERTED_COLUMNS
        if column.startswith("codex_")
    }
    human_indices = [
        layout.insertion_index + INSERTED_COLUMNS.index(column)
        for column in HUMAN_COLUMNS
    ]
    for original, output in zip(original_rows, output_rows):
        reconstructed = (
            list(output[: layout.insertion_index])
            + list(output[layout.insertion_index + inserted_count :])
        )
        if reconstructed != list(original):
            raise ValueError("An original catalogue value or row order changed")
        if any(output[index] != "" for index in human_indices):
            raise ValueError("Every human_* field must be blank")
        for column, index in codex_indices.items():
            value = output[index]
            if column == "codex_notes":
                if not value.strip():
                    raise ValueError("Every row must contain codex_notes")
            elif value not in ALLOWED_VALUES[column]:
                raise ValueError(f"Unexpected {column}: {value}")


def _unknown_rates(
    distributions: dict[str, dict[str, int]], row_count: int
) -> dict[str, float]:
    rates: dict[str, float] = {}
    for column, counts in distributions.items():
        uncertain_value = "unsure" if column == "codex_representative" else "unknown"
        rates[column] = 0.0 if row_count == 0 else counts.get(uncertain_value, 0) / row_count
    return rates


def _sanity_sample(guesses: Sequence[ContextGuess]) -> list[dict[str, Any]]:
    selected: list[int] = []
    targets = [
        ("mode", value)
        for value in ("hike", "walk", "run", "trail_run", "mixed", "ski", "surf", "swim", "cycle", "other", "unknown")
    ] + [
        ("terrain_profile", value)
        for value in ("flat", "rolling", "hilly", "mountainous", "unknown")
    ]
    for attribute, value in targets:
        match = next(
            (index for index, guess in enumerate(guesses) if getattr(guess, attribute) == value),
            None,
        )
        if match is not None and match not in selected:
            selected.append(match)
    return [
        {
            "catalogue_row": index + 2,
            **guesses[index].codex_values(),
        }
        for index in selected
    ]


def build_activity_context(
    export_root: Path,
    research_root: Path,
    repo_root: Path,
    cache_root: Path,
    fallback_cache_roots: Sequence[Path] = (),
    max_dem_tiles: int = MAX_DEM_TILES,
) -> dict[str, Any]:
    export_root = export_root.resolve()
    research_root = research_root.resolve()
    repo_root = repo_root.resolve()
    cache_root = cache_root.resolve()
    if repo_root == research_root or repo_root in research_root.parents:
        raise ValueError("Private research output must be outside the Git repository")
    if repo_root == export_root or repo_root in export_root.parents:
        raise ValueError("Private source export must be outside the Git repository")
    if repo_root == cache_root or repo_root in cache_root.parents:
        raise ValueError("Private DEM cache must be outside the Git repository")
    if export_root == research_root or export_root in research_root.parents:
        raise ValueError("Private research output must not be inside the immutable export")
    source_csv = export_root / "activities.csv"
    activities_root = export_root / "activities"
    output_csv = research_root / "activity-context.csv"
    metadata_path = research_root / "activity-context.metadata.json"
    diagnostics_path = research_root / "activity-context.diagnostics.json"
    if output_csv.exists():
        raise FileExistsError(
            "activity-context.csv already exists; frozen predictions are not overwritten"
        )

    source_csv_hash_before = sha256_file(source_csv)
    recordings_before = source_recording_fingerprint(activities_root)
    header, rows = read_catalogue(source_csv)
    layout = catalogue_layout(header)

    prepared_by_reference: dict[str, PreparedRecording] = {}
    prepared_rows: list[PreparedRecording] = []
    all_tiles: set[tuple[int, int]] = set()
    cache = TerrariumTileCache(
        cache_root,
        fallback_roots=tuple(path.resolve() for path in fallback_cache_roots),
    )
    for row_index, row in enumerate(rows, start=1):
        if len(row) <= max(layout.activity_type_index, layout.filename_index):
            prepared = PreparedRecording(None, None, [], "Catalogue row is incomplete")
        else:
            reference = _normalise_reference(row[layout.filename_index])
            if reference not in prepared_by_reference:
                prepared_by_reference[reference] = prepare_recording(
                    resolve_recording(export_root, reference)
                )
            prepared = prepared_by_reference[reference]
        prepared_rows.append(prepared)
        if prepared.points:
            all_tiles.update(cache.required_tiles(prepared.points))
        if row_index % 25 == 0 or row_index == len(rows):
            print(f"Parsed {row_index}/{len(rows)} catalogue recordings")
    if len(all_tiles) > max_dem_tiles:
        raise RuntimeError(
            f"Terrain plan requires {len(all_tiles)} tiles, exceeding the explicit {max_dem_tiles} tile limit"
        )
    cache.prepare_tiles(all_tiles, concurrency=6)

    terrain_by_reference: dict[str, Any] = {}
    guesses: list[ContextGuess] = []
    terrain_enriched = 0
    for index, (row, prepared) in enumerate(zip(rows, prepared_rows), start=1):
        reference = _normalise_reference(row[layout.filename_index]) if len(row) > layout.filename_index else ""
        if prepared.recording is None:
            guess = unavailable_guess(prepared.parse_error or "Recording could not be analysed")
        else:
            if reference not in terrain_by_reference:
                terrain = unknown_terrain()
                if len(prepared.points) >= 2:
                    elevations = cache.sample(prepared.points)
                    profile = build_terrain_profile(
                        prepared.points, elevations, TERRAIN_VARIANT
                    )
                    terrain = terrain_features(profile)
                terrain_by_reference[reference] = terrain
            terrain = terrain_by_reference[reference]
            if terrain.available:
                terrain_enriched += 1
            activity_type = row[layout.activity_type_index]
            # Activity Name and Activity Description deliberately never cross
            # this inference boundary; only the permitted broad type is passed.
            guess = infer_context(activity_type, prepared.recording, terrain)
        guesses.append(guess)
        if index % 50 == 0 or index == len(rows):
            print(f"Inferred {index}/{len(rows)} activity contexts")

    output_header = (
        header[: layout.insertion_index]
        + list(INSERTED_COLUMNS)
        + header[layout.insertion_index :]
    )
    output_rows = [
        _row_with_context(row, layout.insertion_index, guess)
        for row, guess in zip(rows, guesses)
    ]
    validate_output(header, rows, output_header, output_rows, layout)

    source_csv_hash_after = sha256_file(source_csv)
    recordings_after = source_recording_fingerprint(activities_root)
    if source_csv_hash_before != source_csv_hash_after or recordings_before != recordings_after:
        raise RuntimeError("Immutable Strava source changed during context generation")

    _write_csv(output_csv, output_header, output_rows)
    written_header, written_rows = read_catalogue(output_csv)
    validate_output(header, rows, written_header, written_rows, layout)
    distributions = categorical_distribution(guesses)
    successfully_parsed = sum(prepared.recording is not None for prepared in prepared_rows)
    no_usable_gps = sum(
        prepared.recording is None or not prepared.recording.usable_timestamped_gps
        for prepared in prepared_rows
    )
    diagnostics = {
        "inference_version": INFERENCE_VERSION,
        "row_count": len(rows),
        "recordings_successfully_analysed": successfully_parsed,
        "terrain_enriched_row_count": terrain_enriched,
        "rows_without_usable_gps": no_usable_gps,
        "non_run_type_contribution_count": sum(guess.non_run_type_contributed for guess in guesses),
        "distributions": distributions,
        "unknown_or_unsure_rates": _unknown_rates(distributions, len(rows)),
        "dem": {
            "source": "AWS elevation-tiles-prod Terrarium z15",
            "variant": TERRAIN_VARIANT.id,
            "required_unique_tiles": len(all_tiles),
            "primary_cache_hits": cache.primary_cache_hits,
            "fallback_cache_hits": cache.fallback_cache_hits,
            "downloaded_tiles": cache.downloaded_tiles,
            "downloaded_bytes": cache.downloaded_bytes,
            "failed_tiles": len(cache.failed_tiles),
            "cache_root": str(cache_root),
            "fallback_cache_root_count": len(fallback_cache_roots),
        },
        "sanity_sample": _sanity_sample(guesses),
        "privacy": {
            "names_used_for_inference": False,
            "descriptions_used_for_inference": False,
            "external_lookup_used": False,
            "human_columns_populated": False,
        },
    }
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_head": _git_head(repo_root),
        "inference_version": INFERENCE_VERSION,
        "inference_methodology": inference_methodology(),
        "source_activities_csv_sha256": source_csv_hash_before,
        "generated_activity_context_csv_sha256": sha256_file(output_csv),
        "row_count": len(rows),
        "column_count": len(output_header),
        "recordings_analysed": successfully_parsed,
        "source_recordings_before": recordings_before,
        "source_recordings_after": recordings_after,
        "source_recordings_unchanged": recordings_before == recordings_after,
        "dem": diagnostics["dem"],
        "inference_inputs": {
            "activity_name": False,
            "activity_description": False,
            "human_columns": False,
            "strava_run_subtype": False,
            "non_run_broad_type_prior": True,
        },
    }
    _write_json_atomic(diagnostics_path, diagnostics)
    _write_json_atomic(metadata_path, metadata)
    return {
        "output_csv": str(output_csv),
        "metadata_path": str(metadata_path),
        "diagnostics_path": str(diagnostics_path),
        "metadata": metadata,
        "diagnostics": diagnostics,
    }
