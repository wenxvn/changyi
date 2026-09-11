from __future__ import annotations

from pathlib import Path
import unittest

import app


class StaticAssetBoundaryTests(unittest.TestCase):
    def test_react_shell_and_refresh_routes_are_served_by_flask(self):
        client = app.app.test_client()
        for path in ("/", "/triage", "/resources", "/map", "/trust", "/profile"):
            response = client.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertIn("<div id=\"root\"></div>", response.get_data(as_text=True))

    def test_built_assets_are_served_without_legacy_html_dependencies(self):
        client = app.app.test_client()
        asset = next((Path(app.FRONTEND_DIST / "assets").glob("*.js")), None)
        self.assertIsNotNone(asset)
        response = client.get(f"/assets/{asset.name}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("javascript", response.content_type)

    def test_removed_legacy_assets_are_not_runtime_inputs(self):
        root = Path(app.BASE_DIR)
        for relative_path in (
            "templates/index.html",
            "static/js/app.js",
            "static/css/style.css",
            "static/js/leaflet.js",
            "static/css/leaflet.css",
            "static/images/leaflet-layers.svg",
            "tools/cloudflared.exe",
            "doctors.json",
            "data/test_feedback.jsonl",
        ):
            self.assertFalse((root / relative_path).exists(), relative_path)
