from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RENDERER_ROOT = REPOSITORY_ROOT / "renderers" / "unreal" / "tryfan-reference"


class ReferenceRendererTests(unittest.TestCase):
    def test_manifest_and_preserved_map_match(self) -> None:
        manifest = json.loads(
            (RENDERER_ROOT / "renderer-manifest.json").read_text(encoding="utf-8")
        )
        map_path = RENDERER_ROOT / manifest["unreal"]["map_file"]
        self.assertEqual(map_path.stat().st_size, manifest["unreal"]["map_bytes"])
        self.assertEqual(
            hashlib.sha256(map_path.read_bytes()).hexdigest(),
            manifest["unreal"]["map_sha256"],
        )

    def test_lfs_rule_is_path_specific(self) -> None:
        attributes = (REPOSITORY_ROOT / ".gitattributes").read_text(encoding="utf-8")
        expected = (
            "renderers/unreal/tryfan-reference/Content/Tryfan_Lab004.umap "
            "filter=lfs diff=lfs merge=lfs -text"
        )
        self.assertIn(expected, attributes)
        self.assertNotIn("*.umap filter=lfs", attributes)
        self.assertNotIn("*.uasset filter=lfs", attributes)

    def test_curated_config_excludes_generated_android_secret_section(self) -> None:
        config = (RENDERER_ROOT / "Config" / "DefaultEngine.ini").read_text(
            encoding="utf-8"
        )
        self.assertIn("GeneralProjectSettings", config)
        self.assertNotIn("AndroidFileServer", config)
        self.assertNotIn("SecurityToken", config)
        project = json.loads(
            (RENDERER_ROOT / "TryfanLab004.uproject").read_text(encoding="utf-8")
        )
        plugins = {item["Name"]: item["Enabled"] for item in project["Plugins"]}
        self.assertIs(plugins["AndroidFileServer"], False)

    def test_generated_packages_and_deployments_are_ignored(self) -> None:
        ignore = (RENDERER_ROOT / ".gitignore").read_text(encoding="utf-8")
        for expected in (
            "/Content/Python/",
            "/Content/MeridianLab004/",
            "/Content/MeridianLab009/",
            "/Saved/",
            "/Intermediate/",
            "/Config/DefaultInput.ini",
        ):
            self.assertIn(expected, ignore)

    def test_smoke_validation_never_saves_the_map(self) -> None:
        source = (
            REPOSITORY_ROOT
            / "scripts"
            / "earth_lab"
            / "unreal_validate_reference_renderer.py"
        ).read_text(encoding="utf-8")
        self.assertIn("save_map=False", source)
        self.assertIn('"map_saved_by_validation": False', source)
        self.assertNotIn("save_map(world", source)


if __name__ == "__main__":
    unittest.main()
