"""Resolve active paths from frozen Earth Lab configuration conventions."""
from __future__ import annotations

from pathlib import Path
import sys


SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from meridian_paths import resolve_project_path  # noqa: E402


def resolve_config_value(config_path: Path, value: str) -> Path:
    """Resolve a config value without changing the frozen config text."""
    repository_root = config_path.resolve().parents[2]
    return resolve_project_path(value, repository_root=repository_root)


def resolve_repository_value(repository_root: Path, value: str) -> Path:
    """Resolve a value using an already known repository root."""
    return resolve_project_path(value, repository_root=repository_root)
