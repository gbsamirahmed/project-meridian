"""Local orchestration of the existing GFS builder; one complete catalogue per update."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import tempfile
import time

from PIL import Image
import gfs_weather_builder as core
from gfs_atmospheric import FIELDS, encoding

HOURS = list(range(1, 25))
FIELD_PATHS = {"precipitation": "", "cloud_cover": "cloud-cover", "wind_10m": "wind-10m",
               "temperature_2m": "temperature-2m", "pressure_msl": "pressure-msl",
               **{f.id: f.id.replace("_", "-") for f in FIELDS}}
BASE_RUN_PATTERN = r"[0-9]{8}T(?:00|06|12|18)Z"
RUN_NAME = re.compile(rf"(?P<cycle>{BASE_RUN_PATTERN})(?:-fields-(?P<schema>[0-9a-f]{{12}}))?")
EXPECTED_TILES = 24 * sum(4**z for z in range(4))


def log(message: str) -> None:
    print(f"[{datetime.now(timezone.utc):%Y-%m-%d %H:%MZ}] {message}", flush=True)


@contextmanager
def update_lock(root: Path):
    """Kernel-held lock outside public assets; process exit always releases it."""
    root.mkdir(parents=True, exist_ok=True)
    identity = hashlib.sha256(str(root.resolve()).casefold().encode("utf-8")).hexdigest()[:16]
    lock_path = Path(tempfile.gettempdir()) / f"meridian-gfs-updater-{identity}.lock"
    with lock_path.open("a+b") as handle:
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise BlockingIOError("Another weather updater is already checking/building") from error
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def run_time(run_id: str) -> datetime:
    match = RUN_NAME.fullmatch(run_id)
    if not match:
        raise ValueError("Not a generated GFS cycle directory")
    return datetime.strptime(match.group("cycle"), "%Y%m%dT%HZ").replace(tzinfo=timezone.utc)


def field_schema_id(field_ids=None) -> str:
    selected = set(FIELD_PATHS if field_ids is None else field_ids)
    identity = "\n".join(
        f"{field_id}:{FIELD_PATHS[field_id]}" for field_id in sorted(selected)
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12]


def schema_artifact_name(run_id: str) -> str:
    cycle = run_time(run_id).strftime("%Y%m%dT%HZ")
    return f"{cycle}-fields-{field_schema_id()}"


def iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def read_catalogue(root: Path, require_complete: bool = True) -> dict | None:
    try:
        value = json.loads((root / "latest.json").read_text(encoding="utf-8"))
        field_ids = set(value["fields"])
        if (value["schemaVersion"] != 2 or value["model"] != "NOAA GFS" or
                value["product"] != "pgrb2.0p25" or not isinstance(value["generatedAt"], str) or
                not field_ids or not field_ids.issubset(FIELD_PATHS)):
            raise ValueError("Invalid catalogue identity or fields")
        if require_complete and field_ids != set(FIELD_PATHS):
            raise ValueError("Expected all required fields")
        times = {entry["runTime"] for entry in value["fields"].values()}
        if len(times) != 1:
            raise ValueError("Catalogue mixes runs")
        date = datetime.fromisoformat(times.pop().replace("Z", "+00:00"))
        artifacts = {entry["manifest"].split("/")[0] for entry in value["fields"].values()}
        if len(artifacts) != 1:
            raise ValueError("Catalogue mixes immutable artifacts")
        artifact = artifacts.pop()
        match = RUN_NAME.fullmatch(artifact)
        if (date.tzinfo is None or date.utcoffset() != timedelta(0) or
                run_time(artifact) != date or
                (match.group("schema") is not None and
                 match.group("schema") != field_schema_id(field_ids))):
            raise ValueError("Invalid GFS run time or field schema")
        for key in field_ids:
            subdir = FIELD_PATHS[key]
            entry = value["fields"][key]
            expected_path = "/".join(part for part in (artifact, subdir, "manifest.json") if part)
            if (entry["manifest"] != expected_path or entry["timestepCount"] != 24 or
                    entry["firstValidTime"] != iso(date + timedelta(hours=1)) or
                    entry["lastValidTime"] != iso(date + timedelta(hours=24))):
                raise ValueError("Invalid catalogue coverage/path")
        return value
    except FileNotFoundError:
        return None
    except (OSError, ValueError, KeyError, TypeError) as error:
        log(f"Catalogue unavailable/malformed; immutable runs will be preserved: {error}")
        return None


def checked_path(path: Path, root: Path) -> Path:
    """Never traverse a symlink/junction or delete outside the selected weather root."""
    absolute = path.absolute()
    boundary = root.resolve()
    if absolute == boundary or not absolute.is_relative_to(boundary):
        raise ValueError("Generated path escapes the weather root")
    current = absolute
    while current != boundary:
        if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
            raise ValueError("Generated path contains a link")
        current = current.parent
    if not absolute.resolve().is_relative_to(boundary):
        raise ValueError("Resolved generated path escapes the weather root")
    return absolute


def validate_field(directory: Path, field_id: str, date: datetime, verify_png: bool = True) -> dict:
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    validation = json.loads((directory / "validation.json").read_text(encoding="utf-8"))
    field, tiles = manifest["field"], manifest["tiles"]
    if (manifest["schemaVersion"] != 2 or manifest["model"] != "NOAA GFS" or
            manifest["product"] != "pgrb2.0p25" or manifest["runTime"] != iso(date) or
            field["id"] != field_id or field["nativeResolution"] != {"longitudeDegrees": 0.25, "latitudeDegrees": 0.25} or
            tiles["minZoom"] != 0 or tiles["maxZoom"] != 3 or tiles["tileSize"] != 256 or tiles["format"] != "png"):
        raise ValueError(f"Invalid {field_id} manifest identity/grid")
    contracts = {
        "precipitation": ("APCP", "surface", "mm", "interval-total", "uint16-rg", 0.01, 0),
        "cloud_cover": ("TCDC", "entire atmosphere", "percent", "instantaneous", "uint8-r", 1, 0),
        "temperature_2m": ("TMP", "2 m above ground", "celsius", "instantaneous", "uint16-rg", 0.1, -150),
        "pressure_msl": ("PRMSL", "mean sea level", "hPa", "instantaneous", "uint16-rg", 0.1, 800),
    }
    for atmospheric in FIELDS:
        scale, offset, _ = encoding(atmospheric)
        contracts[atmospheric.id] = (atmospheric.parameter, atmospheric.level, atmospheric.units,
                                   "instantaneous", "uint16-rg", scale, offset)
    if field_id == "wind_10m":
        if (field["kind"] != "vector" or field["sourceLevel"] != "10 m above ground" or
                field["units"] != "m/s" or field["timeSemantics"] != "instantaneous" or
                field["vectorConvention"] != "earth-relative-eastward-northward" or
                tiles["encoding"] != "packed-uv10-rgb" or tiles["componentScale"] != 0.2 or
                tiles["componentBias"] != 512 or tiles["noDataCode"] != 0):
            raise ValueError("Invalid wind contract")
    else:
        expected = contracts[field_id]
        actual = (field["sourceParameter"], field["sourceLevel"], field["units"], field["timeSemantics"],
                  tiles["encoding"], tiles["scale"], tiles["offset"])
        if actual != expected or tiles["noData"] != (255 if field_id == "cloud_cover" else 65535):
            raise ValueError(f"Invalid {field_id} physical encoding")
        for atmospheric in FIELDS:
            if field_id == atmospheric.id and field["verticalReference"] != atmospheric.vertical_reference:
                raise ValueError("Invalid vertical reference")
        if field_id == "pressure_msl" and field.get("verticalReference") != "mean-sea-level":
            raise ValueError("Invalid pressure vertical reference")
    summary = validation["summary"]
    if summary.get("tileFileCount", summary.get("tileCount")) != EXPECTED_TILES:
        raise ValueError(f"{field_id} has no complete validation record")
    if len(manifest["timesteps"]) != 24:
        raise ValueError("Expected f001-f024")
    for hour, step in enumerate(manifest["timesteps"], 1):
        token = f"f{hour:03d}"
        if (step["id"] != token or step["forecastHour"] != hour or
                step["validTime"] != iso(date + timedelta(hours=hour)) or
                step["tileTemplate"] != f"tiles/{token}/{{z}}/{{x}}/{{y}}.png"):
            raise ValueError("Invalid forecast timestep")
        if field_id == "precipitation" and (step["accumulationStart"] != iso(date + timedelta(hours=hour-1)) or
                step["accumulationEnd"] != step["validTime"] or step["accumulationHours"] != 1):
            raise ValueError("Invalid precipitation interval")
        for z in range(4):
            for y in range(2**z):
                for x in range(2**z):
                    path = checked_path(directory / "tiles" / token / str(z) / str(x) / f"{y}.png", directory.resolve())
                    if not path.is_file():
                        raise ValueError(f"Missing {field_id} tile {token}/{z}/{x}/{y}")
                    if verify_png:
                        with Image.open(path) as image:
                            if image.format != "PNG" or image.size != (256, 256) or image.mode != "RGBA":
                                raise ValueError("Invalid numeric PNG")
                            image.verify()
    return manifest


def validate_run(directory: Path, verify_png: bool = True) -> dict:
    date = run_time(directory.name)
    allowed_top = {"tiles", "manifest.json", "validation.json", "source", "atmospheric-source",
                   ".meridian-publishing", *[value for value in FIELD_PATHS.values() if value]}
    if any(entry.name not in allowed_top for entry in directory.iterdir()):
        raise ValueError("Immutable run contains unrecognised top-level content")
    fields = {}
    for field_id, subdir in FIELD_PATHS.items():
        field_directory = directory / subdir
        if not field_directory.is_dir():
            raise ValueError(f"Immutable run is missing required {field_id} data")
        if subdir and any(entry.name not in {"tiles", "manifest.json", "validation.json", "source"}
                          for entry in field_directory.iterdir()):
            raise ValueError(f"Immutable {field_id} contains unrecognised content")
        manifest = validate_field(field_directory, field_id, date, verify_png)
        relative = "/".join(part for part in (directory.name, subdir, "manifest.json") if part)
        fields[field_id] = core.field_catalog_entry(manifest, relative)
    return {"schemaVersion": 2, "model": "NOAA GFS", "product": "pgrb2.0p25",
            "generatedAt": iso(datetime.now(timezone.utc)), "fields": fields}


def clone_file(source: Path, destination: Path) -> dict:
    destination.parent.mkdir(parents=True, exist_ok=True)
    size = source.stat().st_size
    try:
        os.link(source, destination)
        return {"linked": 1, "copied": 0, "logicalBytes": size}
    except OSError:
        shutil.copy2(source, destination)
        return {"linked": 0, "copied": 1, "logicalBytes": size}


def clone_tree(source: Path, destination: Path) -> dict:
    """Clone immutable files with hard links where possible, copying only as fallback."""
    result = {"linked": 0, "copied": 0, "logicalBytes": 0}
    for path in [source, *source.rglob("*")]:
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
            raise ValueError("Reusable generated field contains a link")
        relative = path.relative_to(source)
        target = destination / relative
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        if not path.is_file():
            raise ValueError("Reusable generated field contains an unsupported entry")
        target.parent.mkdir(parents=True, exist_ok=True)
        merge_clone_counts(result, clone_file(path, target))
    return result


def merge_clone_counts(total: dict, added: dict) -> None:
    for key in ("linked", "copied", "logicalBytes"):
        total[key] += added[key]


def stage_reusable_fields(source_run: Path, staged_run: Path, run_id: str) -> dict:
    """Validate and clone reusable fields from exactly one matching GFS initialization."""
    if run_time(source_run.name) != run_time(run_id):
        raise ValueError("GFS artifacts may only be reused within the exact same model cycle")
    date = run_time(run_id)
    result = {"fields": [], "linked": 0, "copied": 0, "logicalBytes": 0}
    staged_run.mkdir(parents=True, exist_ok=True)
    for field_id, subdir in FIELD_PATHS.items():
        source = source_run / subdir
        target = staged_run / subdir
        try:
            validate_field(source, field_id, date)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            log(f"Same-cycle {field_id} is not reusable and will be generated: {error}")
            continue
        if (target / "manifest.json").is_file():
            validate_field(target, field_id, date)
            result["fields"].append(field_id)
            continue
        target.mkdir(parents=True, exist_ok=True)
        merge_clone_counts(result, clone_tree(source / "tiles", target / "tiles"))
        for name in ("manifest.json", "validation.json"):
            merge_clone_counts(result, clone_file(source / name, target / name))
        validate_field(target, field_id, date)
        result["fields"].append(field_id)
    return result


def stage_source_caches(source_run: Path, staged_run: Path) -> dict:
    """Preserve known source caches while publishing a same-cycle schema artifact."""
    result = {"linked": 0, "copied": 0, "logicalBytes": 0}
    candidates = [(source_run / name, staged_run / name) for name in ("source", "atmospheric-source")]
    candidates.extend((source_run / subdir / "source", staged_run / subdir / "source")
                      for subdir in FIELD_PATHS.values() if subdir)
    for source, target in candidates:
        if source.is_dir() and not target.exists():
            merge_clone_counts(result, clone_tree(source, target))
    return result


def cleanup_completed_transaction(root: Path, run_id: str) -> None:
    """Remove completed transaction metadata only after latest names the valid artifact."""
    work = root / f".{run_id}-update-building"
    if not work.is_dir() or not (work / ".meridian-update").is_file():
        return
    if (work / ".meridian-update").read_text() != run_id:
        return
    catalogue = read_catalogue(root)
    artifacts = ({entry["manifest"].split("/")[0] for entry in catalogue["fields"].values()}
                 if catalogue is not None else set())
    if len(artifacts) != 1 or run_time(next(iter(artifacts))) != run_time(run_id):
        return
    artifact = next(iter(artifacts))
    validate_run(root / artifact, verify_png=False)
    remove_generated(work / "latest.json", root)
    remaining = [item for item in work.iterdir() if item.name != ".meridian-update"]
    if not remaining:
        remove_generated(work / ".meridian-update", root)
        work.rmdir()
    else:
        log("Transaction contains preserved non-generated files; marker retained")


def remove_generated(path: Path, root: Path) -> None:
    target = checked_path(path, root)
    if target.is_dir():
        for entry in target.rglob("*"):
            checked_path(entry, root)
        shutil.rmtree(target)
    elif target.exists():
        target.unlink()


def publication_copy(source: str, destination: str) -> str:
    """Hard-link immutable publication files, copying only across filesystems."""
    target = Path(destination)
    if target.exists():
        target.unlink()
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)
    return destination


def publish_catalogue(root: Path, catalogue: dict) -> None:
    """Retry the atomic pointer swap when Windows briefly retains latest.json."""
    for attempt in range(8):
        try:
            core.write_json_atomically(root / "latest.json", catalogue)
            return
        except PermissionError:
            if os.name != "nt" or attempt == 7:
                raise
            if attempt == 0:
                log("latest.json is temporarily busy; retrying atomic publication")
            time.sleep(1)


def promote_run(source: Path, destination: Path, root: Path, run_id: str) -> None:
    """Prefer an atomic rename; Windows watcher contention gets a safe copy fallback."""
    last_error = None
    if not destination.exists():
        for attempt in range(10):
            try:
                os.replace(source, destination)
                return
            except PermissionError as error:
                last_error = error
                if attempt < 9:
                    time.sleep(0.5)
    marker = destination / ".meridian-publishing"
    if destination.exists():
        if not marker.is_file() or marker.read_text() != run_id:
            raise last_error or PermissionError("Immutable destination already exists")
        log(f"Resuming marked copy into immutable run {run_id}")
    else:
        destination.mkdir()
        marker.write_text(run_id)
        log(f"Directory rename remained busy; copying {run_id} before a second full validation")
    try:
        shutil.copytree(
            source, destination, dirs_exist_ok=True, copy_function=publication_copy
        )
        validate_run(destination)
        marker.unlink()
        remove_generated(source, root)
    except Exception:
        # The marker makes a hard-interrupted/partial copy identifiable on restart.
        raise


def repair_staging(work: Path, run_id: str) -> None:
    """Only our marked private transaction is repairable; immutable published runs are not."""
    if (work / ".meridian-update").read_text() != run_id:
        raise ValueError("Unrecognised transaction directory")
    date = run_time(run_id)
    directory = work / run_id
    for field_id, subdir in FIELD_PATHS.items():
        field_dir = directory / subdir
        if not field_dir.exists():
            continue
        try:
            validate_field(field_dir, field_id, date)
        except (OSError, ValueError, KeyError, TypeError):
            # Source downloads live outside this workspace. Unknown contents are
            # preserved rather than swept up in recovery after an interrupted copy.
            allowed = {"tiles", "manifest.json", "validation.json", *[v for v in FIELD_PATHS.values() if v]}
            if any(p.name not in allowed for p in field_dir.iterdir()):
                raise ValueError("Staging contains source/unknown files; leaving it untouched")
            log(f"Discarding incomplete staged {field_id}; it will be rebuilt")
            remove_generated(field_dir, work)
    # Interrupted field builders may leave their own scratch directory behind.
    for child in work.iterdir():
        if child.is_dir() and child.name.startswith(f".{run_id}-") and child.name.endswith("-building"):
            if any(p.name not in {"tiles", "manifest.json", "validation.json"} for p in child.iterdir()):
                continue
            remove_generated(child, work)


def prune_stale_transactions(root: Path, current: str) -> list[str]:
    """Remove only generated content from marked transactions older than latest."""
    removed = []
    for work in root.iterdir():
        match = re.fullmatch(r"\.(\d{8}T(?:00|06|12|18)Z)-update-building", work.name)
        if not work.is_dir() or not match or match.group(1) >= current:
            continue
        run_id = match.group(1)
        try:
            if (work / ".meridian-update").read_text() != run_id:
                continue
            repair_staging(work, run_id)
            directory = work / run_id
            if directory.exists():
                for _field_id, subdir in FIELD_PATHS.items():
                    field_dir = directory / subdir
                    if not field_dir.exists():
                        continue
                    if subdir:
                        remove_generated(field_dir, root)
                    else:
                        for name in ("tiles", "manifest.json", "validation.json"):
                            remove_generated(field_dir / name, root)
                if directory.exists() and not any(directory.iterdir()):
                    directory.rmdir()
            remove_generated(work / "latest.json", root)
            # Keep the marker when unknown/source files remain so future cleanup
            # can still identify the transaction without guessing ownership.
            remaining = [item for item in work.iterdir() if item.name != ".meridian-update"]
            if not remaining:
                remove_generated(work / ".meridian-update", root)
                work.rmdir()
                removed.append(run_id)
                log(f"Pruned stale generated transaction {run_id}")
            else:
                log(f"Preserved non-generated contents in stale transaction {run_id}")
        except (OSError, ValueError, KeyError, TypeError) as error:
            log(f"Stale transaction cleanup deferred for {run_id}: {error}")
    return removed


def prune_runs(root: Path) -> list[str]:
    catalogue = read_catalogue(root)
    if catalogue is None:
        return []
    current = next(iter(catalogue["fields"].values()))["manifest"].split("/")[0]
    current_time = run_time(current)
    candidates = sorted(
        (path for path in root.iterdir()
         if path.is_dir() and RUN_NAME.fullmatch(path.name) and path.name != current
         and run_time(path.name) <= current_time),
        key=lambda path: (run_time(path.name), path.name),
        reverse=True,
    )
    previous = None
    for candidate in candidates:
        try:
            validate_run(candidate, verify_png=False)
            previous = candidate.name
            break
        except (OSError, ValueError, KeyError, TypeError):
            pass
    removed = []
    for candidate in candidates:
        if candidate.name == previous:
            continue
        # Re-read the live pointer immediately before any destructive operation.
        live = read_catalogue(root)
        if live is None or any(e["manifest"].split("/")[0] == candidate.name for e in live["fields"].values()):
            continue
        try:
            checked_path(candidate, root)
            recognized = False
            for field_id, subdir in FIELD_PATHS.items():
                directory = candidate / subdir
                manifest_path = directory / "manifest.json"
                if not manifest_path.is_file():
                    continue
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                identity = manifest.get("field", manifest.get("variable", {})).get("id")
                if (identity != field_id or manifest.get("model") != "NOAA GFS" or
                        manifest.get("product") != "pgrb2.0p25" or manifest.get("runTime") != iso(run_time(candidate.name))):
                    continue
                for name in ("tiles", "manifest.json", "validation.json"):
                    remove_generated(directory / name, root)
                if subdir and not any(directory.iterdir()):
                    directory.rmdir()
                recognized = True
            if recognized:
                if not any(candidate.iterdir()):
                    candidate.rmdir()
                log(f"Pruned generated weather {candidate.name}; any source caches were preserved")
                removed.append(candidate.name)
        except (OSError, ValueError, KeyError, TypeError) as error:
            log(f"Cleanup deferred for {candidate.name}: {error}")
    log(f"Retention: current {current}; previous {previous or 'none yet'}")
    return removed


def update_once(args: argparse.Namespace) -> dict:
    root = args.output_root.resolve()
    started = time.monotonic()
    with update_lock(root):
        current = read_catalogue(root, require_complete=False)
        current_is_complete = bool(current and set(current["fields"]) == set(FIELD_PATHS))
        if current and not current_is_complete:
            log(f"Published catalogue has {len(current['fields'])} of {len(FIELD_PATHS)} required fields; retaining it until a same-cycle completion or newer run is ready")
        current_time = datetime.fromisoformat(next(iter(current["fields"].values()))["runTime"].replace("Z", "+00:00")) if current else None
        current_id = current_time.strftime("%Y%m%dT%HZ") if current_time else None
        discovery_floor = (current_time if current_is_complete or current_time is None
                           else current_time - timedelta(seconds=1))
        core.fetch_text.cache_clear()  # Incomplete inventories must be re-probed next hour.
        options = argparse.Namespace(**{**vars(args), "require_all_fields": True})
        resolution = core.resolve_run(options, HOURS, newer_than=discovery_floor)
        if resolution is None:
            log(f"No newer usable run; retaining {iso(current_time) if current_time else 'existing data'}")
            if not args.check_only and current_is_complete:
                try:
                    if current_id:
                        cleanup_completed_transaction(root, current_id)
                        prune_stale_transactions(root, current_id)
                    prune_runs(root)
                except (OSError, ValueError) as error:
                    log(f"Cleanup deferred; live forecast remains valid: {error}")
            return {"generated": False, "run": iso(current_time) if current_time else None}

        name = resolution.run_time.strftime("%Y%m%dT%HZ")
        log(f"Newest usable {len(FIELD_PATHS)}-field candidate: {name}")
        if args.check_only:
            return {"generated": False, "candidate": name}

        base_destination = checked_path(root / name, root)
        schema_destination = checked_path(root / schema_artifact_name(name), root)
        work = checked_path(root / f".{name}-update-building", root)
        generated = False
        reuse = {"fields": [], "linked": 0, "copied": 0, "logicalBytes": 0}
        migration_source = None
        destination = base_destination
        catalogue = None
        complete_existing = False

        # A schema-qualified artifact may be the completed result of a prior
        # transaction whose atomic latest.json publication was interrupted.
        for candidate in (schema_destination, base_destination):
            marker = candidate / ".meridian-publishing"
            if not candidate.exists() or marker.exists():
                continue
            try:
                catalogue = validate_run(candidate)
                destination = candidate
                complete_existing = True
                log(f"Reusing complete immutable artifact {candidate.name}")
                break
            except (OSError, ValueError, KeyError, TypeError):
                pass

        if not complete_existing and base_destination.exists():
            try:
                validate_run(base_destination)
            except (OSError, ValueError, KeyError, TypeError) as error:
                migration_source = base_destination
                destination = schema_destination
                log(f"Completing occupied same-cycle {name} as {destination.name} "
                    f"in a private transaction: {error}")

        publishing_marker = destination / ".meridian-publishing"
        if (destination.exists() and not publishing_marker.exists() and
                not any(destination.iterdir()) and
                (work / ".meridian-update").is_file() and
                (work / ".meridian-update").read_text() == name):
            destination.rmdir()
            log(f"Recovered empty interrupted immutable destination {destination.name}")

        if not complete_existing:
            if not work.exists():
                work.mkdir()
                (work / ".meridian-update").write_text(name)
            elif not (work / ".meridian-update").exists():
                if any(work.iterdir()):
                    raise ValueError("Unrecognised non-empty transaction directory; leaving it untouched")
                (work / ".meridian-update").write_text(name)
            repair_staging(work, name)
            if migration_source is not None:
                reuse = stage_reusable_fields(migration_source, work / name, name)
                log(f"Staged {len(reuse['fields'])} validated same-cycle field(s): "
                    f"{reuse['linked']} hard-linked files, {reuse['copied']} copied files")
            build_options = argparse.Namespace(**{**vars(args), "output_root": work, "source_cache_root": root})
            core.build_resolved_run(build_options, resolution, HOURS)
            if migration_source is not None:
                cache_reuse = stage_source_caches(migration_source, work / name)
                merge_clone_counts(reuse, cache_reuse)
            validate_run(work / name)
            promote_run(work / name, destination, root, destination.name)
            catalogue = validate_run(destination, verify_png=False)
            generated = True

        publish_catalogue(root, catalogue)
        log(f"Published complete {destination.name} atomically in {time.monotonic() - started:.1f}s")
        try:
            cleanup_completed_transaction(root, name)
        except (OSError, ValueError) as error:
            log(f"Transaction metadata cleanup deferred: {error}")
        try:
            prune_stale_transactions(root, name)
            removed = prune_runs(root)
        except (OSError, ValueError) as error:
            log(f"Cleanup deferred; published forecast remains valid: {error}")
            removed = []
        return {"generated": generated, "run": iso(resolution.run_time),
                "artifact": destination.name, "removed": removed,
                "reusedFields": reuse["fields"], "hardLinkedFiles": reuse["linked"],
                "copiedFiles": reuse["copied"], "reusedLogicalBytes": reuse["logicalBytes"],
                "seconds": round(time.monotonic() - started, 2)}


def run_command(args: argparse.Namespace) -> None:
    if core.parse_hours(args.hours) != HOURS:
        raise ValueError("Automatic GFS publication requires exactly --hours 1-24")
    if not math.isfinite(args.poll_minutes) or args.poll_minutes < 15:
        raise ValueError("--poll-minutes must be at least 15")
    if args.watch and args.run:
        raise ValueError("--watch discovers new cycles; omit --run")
    def terminate(_signum, _frame):
        raise KeyboardInterrupt
    prior = signal.signal(signal.SIGTERM, terminate)
    try:
        while True:
            try:
                result = update_once(args)
                log(json.dumps(result))
            except BlockingIOError as error:
                log(str(error))
                if not args.watch:
                    raise SystemExit(2) from error
            except Exception as error:
                log(f"Update failed; live catalogue unchanged: {type(error).__name__}: {error}")
                if not args.watch:
                    raise SystemExit(1) from error
            if not args.watch:
                break
            log(f"Next check in {args.poll_minutes:g} minutes")
            time.sleep(args.poll_minutes * 60)
    except KeyboardInterrupt:
        log("Weather updater stopped; live catalogue preserved")
    finally:
        signal.signal(signal.SIGTERM, prior)
