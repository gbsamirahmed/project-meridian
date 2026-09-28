"""Resolve Meridian's external storage roots without exposing them to web code.

This module is deliberately small.  It provides one shared convention for local
Python tooling while preserving the repository's historical sibling-directory
layout as the default.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Mapping


DATA_ROOT_ENV = "MERIDIAN_DATA_ROOT"
PRIVATE_ROOT_ENV = "MERIDIAN_PRIVATE_ROOT"


def default_repository_root() -> Path:
    """Return the project-meridian root containing this scripts directory."""
    return Path(__file__).resolve().parents[1]


def _resolved_root(
    value: str | None,
    *,
    fallback: Path,
    variable: str,
) -> tuple[Path, str]:
    configured = value.strip() if value is not None else ""
    if not configured:
        return fallback.resolve(), "sibling_default"
    path = Path(configured).expanduser()
    if not path.is_absolute():
        raise ValueError(f"{variable} must be an absolute path, got: {configured}")
    return path.resolve(), "environment"


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _require(path: Path, *, label: str, variable: str) -> None:
    if not path.is_dir():
        raise FileNotFoundError(
            f"Required Meridian {label} root does not exist: {path}. "
            f"Set {variable} to an existing absolute directory."
        )


def _child(root: Path, parts: tuple[str | os.PathLike[str], ...], *, label: str) -> Path:
    candidate = root.joinpath(*parts).resolve()
    if not _is_within(candidate, root):
        raise ValueError(f"Meridian {label} path escapes its configured root: {candidate}")
    return candidate


@dataclass(frozen=True)
class StorageRoots:
    """Resolved local roots plus where each value came from."""

    repository: Path
    data: Path
    private: Path
    data_source: str
    private_source: str

    def data_path(
        self,
        *parts: str | os.PathLike[str],
        must_exist: bool = False,
    ) -> Path:
        path = _child(self.data, parts, label="data")
        if must_exist and not path.exists():
            raise FileNotFoundError(f"Required Meridian data path does not exist: {path}")
        return path

    def private_path(
        self,
        *parts: str | os.PathLike[str],
        must_exist: bool = False,
    ) -> Path:
        path = _child(self.private, parts, label="private")
        if must_exist and not path.exists():
            raise FileNotFoundError(f"Required Meridian private path does not exist: {path}")
        return path

    def as_dict(self) -> dict[str, str]:
        return {
            "repository_root": str(self.repository),
            "data_root": str(self.data),
            "data_root_source": self.data_source,
            "private_root": str(self.private),
            "private_root_source": self.private_source,
        }


def resolve_storage_roots(
    *,
    repository_root: Path | None = None,
    environ: Mapping[str, str] | None = None,
    require_data: bool = False,
    require_private: bool = False,
) -> StorageRoots:
    """Resolve configured roots while keeping generated/private data outside Git."""
    repository = (repository_root or default_repository_root()).resolve()
    environment = os.environ if environ is None else environ
    data, data_source = _resolved_root(
        environment.get(DATA_ROOT_ENV),
        fallback=repository.parent / "meridian-data",
        variable=DATA_ROOT_ENV,
    )
    private, private_source = _resolved_root(
        environment.get(PRIVATE_ROOT_ENV),
        fallback=repository.parent / "meridian-private",
        variable=PRIVATE_ROOT_ENV,
    )
    for label, path in (("data", data), ("private", private)):
        if path == repository or _is_within(path, repository):
            raise ValueError(
                f"Meridian {label} root must be outside the Git repository: {path}"
            )
    if data == private or _is_within(data, private) or _is_within(private, data):
        raise ValueError(
            "Meridian data and private roots must be separate, non-overlapping directories"
        )
    if require_data:
        _require(data, label="data", variable=DATA_ROOT_ENV)
    if require_private:
        _require(private, label="private", variable=PRIVATE_ROOT_ENV)
    return StorageRoots(repository, data, private, data_source, private_source)


def resolve_project_path(
    value: str | os.PathLike[str],
    *,
    roots: StorageRoots | None = None,
    repository_root: Path | None = None,
    must_exist: bool = False,
) -> Path:
    """Resolve a repository path, including historical sibling-root conventions.

    Existing configs such as ``../meridian-data/earth-lab/...`` retain their
    current meaning.  When MERIDIAN_DATA_ROOT is configured, that legacy prefix
    maps to the configured root without changing the historical config file.
    Ordinary relative paths continue to resolve from the repository root.
    """
    resolved_roots = roots or resolve_storage_roots(repository_root=repository_root)
    path = Path(value)
    if path.is_absolute():
        result = path.resolve()
    else:
        parts = path.parts
        if len(parts) >= 2 and parts[0] == ".." and parts[1].casefold() == "meridian-data":
            result = resolved_roots.data_path(*parts[2:])
        elif len(parts) >= 2 and parts[0] == ".." and parts[1].casefold() == "meridian-private":
            result = resolved_roots.private_path(*parts[2:])
        else:
            result = (resolved_roots.repository / path).resolve()
            if not _is_within(result, resolved_roots.repository):
                raise ValueError(
                    "Repository-relative Meridian path escapes the Git repository; "
                    "use MERIDIAN_DATA_ROOT, MERIDIAN_PRIVATE_ROOT, or an explicit "
                    f"absolute path: {result}"
                )
    if must_exist and not result.exists():
        raise FileNotFoundError(f"Required Meridian path does not exist: {result}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve Meridian local storage roots")
    parser.add_argument("--require-data", action="store_true")
    parser.add_argument("--require-private", action="store_true")
    arguments = parser.parse_args()
    roots = resolve_storage_roots(
        require_data=arguments.require_data,
        require_private=arguments.require_private,
    )
    print(json.dumps(roots.as_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
