from __future__ import annotations

import time
import unittest

IMPORT_ERROR = None
try:
    from app import create_app
    from config.settings import TestingConfig
    from extensions import db
    from models.core import Category, User
    from models.marketplace import ProviderProfile, ProviderService, Service
    from services.auth_service import password_hash
except ModuleNotFoundError as exc:
    IMPORT_ERROR = exc


class Phase8RuntimeConfig(TestingConfig if IMPORT_ERROR is None else object):
    if IMPORT_ERROR is None:
        APP_REQUIRE_EMAIL_VERIFICATION = False
        APP_ADMIN_MFA_REQUIRED = False


@unittest.skipIf(IMPORT_ERROR is not None, f"Phase 8 runtime dependencies are not installed: {IMPORT_ERROR}")
class Phase8ReleaseRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(Phase8RuntimeConfig)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            category = Category(name="Plumbing", slug="plumbing", icon="fa-wrench", is_active=1)
            db.session.add(category); db.session.flush()
            service = Service(category_id=category.id, name="Plumber", slug="plumber", is_active=1)
            db.session.add(service); db.session.flush()
            provider = User(name="Provider", email="provider8@example.com", password_hash=password_hash("phase eight provider password"), role="provider", status="active", session_version=1)
            customer = User(name="Customer", email="customer8@example.com", password_hash=password_hash("phase eight customer password"), role="customer", status="active", session_version=1)
            db.session.add_all([provider, customer]); db.session.flush()
            db.session.add(ProviderProfile(user_id=provider.id, headline="Plumber", about="Local plumber", service_area="Central", verification_status="verified"))
            db.session.add(ProviderService(provider_user_id=provider.id, service_id=service.id, title="Plumbing repair", is_active=1))
            db.session.commit()
            self.provider_id = int(provider.id)
            self.customer_id = int(customer.id)

    def tearDown(self):
        with self.app.app_context():
            db.session.remove(); db.drop_all()

    def login_as(self, user_id: int):
        now = int(time.time())
        with self.client.session_transaction() as sess:
            sess.clear(); sess["user_id"] = user_id; sess["session_version"] = 1
            sess["_created_at"] = now; sess["_last_activity"] = now; sess["_rotated_at"] = now; sess["_nonce"] = "phase8"

    def test_public_health_error_and_search_surfaces(self):
        self.assertEqual(self.client.get("/health").status_code, 200)
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/search.php?q=Plumber").status_code, 200)
        self.assertEqual(self.client.get("/does-not-exist").status_code, 404)

    def test_role_boundaries_and_provider_profile(self):
        self.login_as(self.customer_id)
        self.assertEqual(self.client.get("/provider/profile.php").status_code, 403)
        self.assertEqual(self.client.get("/admin/index.php").status_code, 403)
        self.login_as(self.provider_id)
        self.assertEqual(self.client.get("/provider/profile.php").status_code, 200)
        self.assertEqual(self.client.get("/customer/dashboard.php").status_code, 403)

    def test_favorite_endpoint_requires_customer_and_keeps_json_contract(self):
        self.login_as(self.customer_id)
        response = self.client.post("/ajax/favorite.php", data={"target_user_id": self.provider_id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"ok": True, "favorite": True})


if __name__ == "__main__":
    unittest.main()
