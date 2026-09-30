from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

IMPORT_ERROR = None
try:
    from app import create_app
    from config.settings import TestingConfig
except ModuleNotFoundError as exc:
    IMPORT_ERROR = exc



ROOT = Path(__file__).resolve().parents[2]


class Phase2FoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if IMPORT_ERROR is not None:
            raise unittest.SkipTest(f"Phase 2 runtime dependencies are not installed: {IMPORT_ERROR}")
        cls.app = create_app(TestingConfig)
        cls.client = cls.app.test_client()

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})
        self.assertEqual(response.headers.get("Cache-Control"), "no-store, max-age=0")

    def test_security_headers_are_applied(self):
        response = self.client.get("/health")
        self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(response.headers.get("X-Frame-Options"), "DENY")
        self.assertEqual(response.headers.get("Referrer-Policy"), "strict-origin-when-cross-origin")
        self.assertIn("Content-Security-Policy-Report-Only", response.headers)

    def test_legacy_error_routes_preserve_status(self):
        self.assertEqual(self.client.get("/403.php").status_code, 403)
        self.assertEqual(self.client.get("/404.php").status_code, 404)
        self.assertEqual(self.client.get("/does-not-exist").status_code, 404)

    def test_existing_static_assets_are_served_without_rewrite(self):
        css_path = ROOT / "assets" / "css" / "style.css"
        js_path = ROOT / "assets" / "js" / "app.js"
        css_before = hashlib.sha256(css_path.read_bytes()).hexdigest()
        js_before = hashlib.sha256(js_path.read_bytes()).hexdigest()
        css_response = self.client.get("/assets/css/style.css")
        js_response = self.client.get("/assets/js/app.js")
        self.assertEqual(css_response.status_code, 200)
        self.assertEqual(js_response.status_code, 200)
        self.assertEqual(hashlib.sha256(css_response.data).hexdigest(), css_before)
        self.assertEqual(hashlib.sha256(js_response.data).hexdigest(), js_before)

    def test_blueprint_namespaces_are_registered(self):
        expected = {"health", "main", "auth", "customer", "provider", "business", "admin", "billing", "api", "webhooks"}
        self.assertTrue(expected.issubset(set(self.app.blueprints)))


if __name__ == "__main__":
    unittest.main()
