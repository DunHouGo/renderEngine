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

    def test_packed_arm_orm_channel_mapping(self) -> None:
        package = pbr_helper.PBRPackage("packed")
        package.selected = {"orm": "/tmp/packed_orm.png"}
        self.assertEqual(package.get_channel_map()["ao"], ("/tmp/packed_orm.png", "r"))
        self.assertEqual(package.get_channel_map()["roughness"], ("/tmp/packed_orm.png", "g"))
        self.assertEqual(package.get_channel_map()["metalness"], ("/tmp/packed_orm.png", "b"))
        self.assertEqual(package.expand_packed_channels()["roughness"], ("/tmp/packed_orm.png", "g"))
        self.assertEqual(pbr_helper.classify_pbr_texture("Fabric_Opacity.tif"), "alpha")
        # 对齐 rsbumpmap_settings.json：coat 系复合词是独立通道，长词优先于尾缀短词。
        self.assertEqual(pbr_helper.classify_pbr_texture("Coat_Normal.tif"), "coat_normal")
        self.assertEqual(pbr_helper.classify_pbr_texture("Mat_4k_clearcoat_normal.tif"), "coat_normal")
        self.assertEqual(pbr_helper.classify_pbr_texture("Mat_4k_coating_roughness.tif"), "coat_roughness")
        self.assertEqual(pbr_helper.classify_pbr_texture("Mat_4k_coat_bump.tif"), "coat_bump")
        self.assertEqual(pbr_helper.classify_pbr_texture("Mat_4k_coatweight.tif"), "coat_weight")
        self.assertEqual(pbr_helper.classify_pbr_texture("Mat_4k_coat.tif"), "coat")
        self.assertEqual(pbr_helper.classify_pbr_texture("Mat_4k_anisotropy_angle.tif"), "anisotropy_angle")
        self.assertEqual(pbr_helper.classify_pbr_texture("Mat_4k_anisotropyrotation.tif"), "anisotropy_angle")
        self.assertEqual(pbr_helper.classify_pbr_texture("Mat_4k_flowmap.exr"), "anisotropy_angle")
        self.assertEqual(pbr_helper.classify_pbr_texture("Mat_4k_anisolevel.tif"), "anisotropy")
        # RSBumpMap 单字母与短词通道。
        self.assertEqual(pbr_helper.classify_pbr_texture("Brick_2k_n.tif"), "normal")
        self.assertEqual(pbr_helper.classify_pbr_texture("Brick_2k_em.tif"), "emission")
        self.assertEqual(pbr_helper.classify_pbr_texture("Brick_2k_trans.png"), "transmission")
        # edgetint 归入 specular（反射工作流）而非 metalness。
        self.assertEqual(pbr_helper.classify_pbr_texture("Gold_4k_edgetint.tif"), "specular")
        self.assertEqual(pbr_helper.classify_pbr_texture("Gold_4k_metalcolor.tif"), "metalness")

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
