# -*- coding: utf-8 -*-
"""Test PBR filename detection without loading Cinema 4D."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


HELPER_PATH = Path(__file__).resolve().parents[1] / "utils" / "pbr_helper.py"


def load_pbr_helper():
    """Load ``pbr_helper`` as a standalone module."""
    spec = importlib.util.spec_from_file_location("pbr_helper_standalone", HELPER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {HELPER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


pbr_helper = load_pbr_helper()


class TestGSGMapDetection(unittest.TestCase):
    """GSG fabric sets use compound tokens such as specularlevel."""

    def test_detect_map_type_from_gsg_names(self) -> None:
        cases = {
            "GSG_MC088_A004_WarmGrayWoolFelt_4k_basecolor.tif": "diffuse",
            "GSG_MC088_A004_WarmGrayWoolFelt_4k_normal.tif": "normal",
            "GSG_MC088_A004_WarmGrayWoolFelt_4k_roughness.tif": "roughness",
            "GSG_MC088_A004_WarmGrayWoolFelt_4k_specularlevel.tif": "specular",
            "GSG_MC088_A004_WarmGrayWoolFelt_4k_scatteringweight.tif": "subsurface",
            "GSG_MC088_A004_WarmGrayWoolFelt_4k_preview.png": None,
            "GSG_MC088_A004_WarmGrayWoolFelt_4k_previewclose.png": None,
        }
        for filename, expected in cases.items():
            tokens = pbr_helper.tokenize(filename)
            self.assertEqual(pbr_helper.detect_map_type(tokens), expected, filename)

    def test_material_descriptor_does_not_override_channel(self) -> None:
        tokens = pbr_helper.tokenize("GSG_Metal_4k_basecolor.tif")
        self.assertEqual(pbr_helper.detect_map_type(tokens), "diffuse")
        self.assertEqual(pbr_helper.classify_pbr_texture("GSG_Metal_Vol1_4k_normal.tif"), "normal")
        self.assertEqual(pbr_helper.classify_pbr_texture("rock_roughness.png"), "roughness")
        self.assertIsNone(pbr_helper.classify_pbr_texture("random_photo.jpg"))

    def test_word_boundary_avoids_short_keyword_false_positive(self) -> None:
        self.assertEqual(pbr_helper.classify_pbr_texture("Wood_Roughness.tif"), "roughness")
        self.assertNotEqual(pbr_helper.classify_pbr_texture("Wood_Roughness.tif"), "normal")
        self.assertEqual(pbr_helper.classify_pbr_texture("Fabric_Opacity.tif"), "alpha")
        # coat_normal 仍按主法线通道识别，避免短词 coat 抢先。
        self.assertEqual(pbr_helper.classify_pbr_texture("Coat_Normal.tif"), "normal")

    def test_package_from_gsg_folder(self) -> None:
        names = (
            "GSG_MC088_A004_WarmGrayWoolFelt_4k_basecolor.tif",
            "GSG_MC088_A004_WarmGrayWoolFelt_4k_normal.tif",
            "GSG_MC088_A004_WarmGrayWoolFelt_4k_roughness.tif",
            "GSG_MC088_A004_WarmGrayWoolFelt_4k_specularlevel.tif",
            "GSG_MC088_A004_WarmGrayWoolFelt_4k_scatteringweight.tif",
            "GSG_MC088_A004_WarmGrayWoolFelt_4k_preview.png",
            "GSG_MC088_A004_WarmGrayWoolFelt_4k_previewclose.png",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            for name in names:
                (folder / name).write_bytes(b"")
            package = pbr_helper.pbr_from_file(folder / names[0])
            self.assertIsNotNone(package)
            maps = package.get_valid_dict()
            self.assertEqual(
                set(maps),
                {"diffuse", "normal", "roughness", "specular", "subsurface"},
            )
            self.assertTrue(maps["diffuse"].endswith("basecolor.tif"))
            self.assertTrue(maps["specular"].endswith("specularlevel.tif"))
            self.assertTrue(maps["subsurface"].endswith("scatteringweight.tif"))


if __name__ == "__main__":
    unittest.main()
