from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class StaticAssetBoundaryTests(unittest.TestCase):
    def test_legacy_favicon_is_declared_and_present(self):
        template = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
        favicon = ROOT / "static" / "favicon.svg"

        self.assertIn('rel="icon"', template)
        self.assertIn('/static/favicon.svg', template)
        self.assertTrue(favicon.is_file())
        self.assertIn('<svg', favicon.read_text(encoding="utf-8"))

    def test_leaflet_layers_control_uses_a_repository_owned_asset(self):
        stylesheet = (ROOT / "static" / "css" / "leaflet.css").read_text(encoding="utf-8")

        self.assertIn('/static/images/leaflet-layers.svg', stylesheet)
        self.assertNotIn('images/layers.png', stylesheet)
        self.assertNotIn('images/layers-2x.png', stylesheet)
        self.assertTrue((ROOT / "static" / "images" / "leaflet-layers.svg").is_file())
