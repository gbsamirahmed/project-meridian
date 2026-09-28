from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from meridian_paths import resolve_project_path, resolve_storage_roots


class StorageRootTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.parent = Path(self.temporary.name).resolve()
        self.repository = self.parent / "project-meridian"
        self.repository.mkdir()

    def test_defaults_preserve_sibling_layout_without_requiring_private_root(self) -> None:
        (self.parent / "meridian-data").mkdir()
        roots = resolve_storage_roots(
            repository_root=self.repository,
            environ={},
            require_data=True,
        )
        self.assertEqual(roots.data, self.parent / "meridian-data")
        self.assertEqual(roots.private, self.parent / "meridian-private")
        self.assertEqual(roots.data_source, "sibling_default")
        self.assertFalse(roots.private.exists())

    def test_absolute_environment_overrides_are_supported(self) -> None:
        data = self.parent / "world-data"
        private = self.parent / "personal-data"
        data.mkdir()
        private.mkdir()
        roots = resolve_storage_roots(
            repository_root=self.repository,
            environ={
                "MERIDIAN_DATA_ROOT": str(data),
                "MERIDIAN_PRIVATE_ROOT": str(private),
            },
            require_data=True,
            require_private=True,
        )
        self.assertEqual(roots.data, data)
        self.assertEqual(roots.private, private)
        self.assertEqual(roots.data_source, "environment")
        self.assertEqual(roots.private_source, "environment")

    def test_relative_environment_root_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be an absolute path"):
            resolve_storage_roots(
                repository_root=self.repository,
                environ={"MERIDIAN_DATA_ROOT": "relative-data"},
            )

    def test_roots_inside_repository_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "outside the Git repository"):
            resolve_storage_roots(
                repository_root=self.repository,
                environ={"MERIDIAN_DATA_ROOT": str(self.repository / "generated")},
            )

    def test_data_and_private_roots_must_not_overlap(self) -> None:
        data = self.parent / "world-data"
        private = data / "private"
        with self.assertRaisesRegex(ValueError, "separate, non-overlapping"):
            resolve_storage_roots(
                repository_root=self.repository,
                environ={
                    "MERIDIAN_DATA_ROOT": str(data),
                    "MERIDIAN_PRIVATE_ROOT": str(private),
                },
            )

    def test_required_missing_root_fails_clearly(self) -> None:
        with self.assertRaisesRegex(FileNotFoundError, "MERIDIAN_PRIVATE_ROOT"):
            resolve_storage_roots(
                repository_root=self.repository,
                environ={},
                require_private=True,
            )

    def test_legacy_data_convention_maps_to_configured_root(self) -> None:
        data = self.parent / "relocated-data"
        data.mkdir()
        roots = resolve_storage_roots(
            repository_root=self.repository,
            environ={"MERIDIAN_DATA_ROOT": str(data)},
        )
        result = resolve_project_path(
            "../meridian-data/earth-lab/tryfan-009",
            roots=roots,
        )
        self.assertEqual(result, data / "earth-lab" / "tryfan-009")

    def test_legacy_private_convention_maps_to_configured_root(self) -> None:
        private = self.parent / "relocated-private"
        private.mkdir()
        roots = resolve_storage_roots(
            repository_root=self.repository,
            environ={"MERIDIAN_PRIVATE_ROOT": str(private)},
        )
        result = resolve_project_path(
            "../meridian-private/traverse/private-route.gpx",
            roots=roots,
        )
        self.assertEqual(result, private / "traverse" / "private-route.gpx")

    def test_ordinary_repository_relative_and_absolute_paths_are_preserved(self) -> None:
        roots = resolve_storage_roots(repository_root=self.repository, environ={})
        self.assertEqual(
            resolve_project_path("docs/architecture.md", roots=roots),
            self.repository / "docs" / "architecture.md",
        )
        absolute = self.parent / "independent.json"
        self.assertEqual(resolve_project_path(absolute, roots=roots), absolute)

    def test_child_paths_cannot_escape_storage_roots(self) -> None:
        roots = resolve_storage_roots(repository_root=self.repository, environ={})
        with self.assertRaisesRegex(ValueError, "escapes its configured root"):
            roots.data_path("..", "outside")

    def test_repository_relative_paths_cannot_escape_repository(self) -> None:
        roots = resolve_storage_roots(repository_root=self.repository, environ={})
        with self.assertRaisesRegex(ValueError, "escapes the Git repository"):
            resolve_project_path("../unclassified-data", roots=roots)

    def test_must_exist_checks_resolved_storage_path(self) -> None:
        data = self.parent / "world-data"
        data.mkdir()
        roots = resolve_storage_roots(
            repository_root=self.repository,
            environ={"MERIDIAN_DATA_ROOT": str(data)},
        )
        with self.assertRaisesRegex(FileNotFoundError, "Required Meridian path"):
            resolve_project_path(
                "../meridian-data/missing-product.json",
                roots=roots,
                must_exist=True,
            )

    def test_resolver_does_not_mutate_process_environment(self) -> None:
        before = dict(os.environ)
        resolve_storage_roots(repository_root=self.repository, environ={})
        self.assertEqual(dict(os.environ), before)


if __name__ == "__main__":
    unittest.main()
