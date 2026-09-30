from __future__ import annotations

import time
import unittest
from datetime import datetime, timedelta
from decimal import Decimal

IMPORT_ERROR = None
try:
    from app import create_app
    from config.settings import TestingConfig
    from extensions import db
    from models.billing import FeaturedListing, LeadWallet, Subscription, SubscriptionPlan
    from models.core import Category, User
    from models.marketplace import ProviderProfile, ProviderService, RequestStatusHistory, Review, Service, ServiceRequest
    from services.marketplace_service import current_subscription
except ModuleNotFoundError as exc:  # constrained audit environments may not have pip access
    IMPORT_ERROR = exc


class Phase5TestingConfig(TestingConfig if IMPORT_ERROR is None else object):
    if IMPORT_ERROR is None:
        APP_ADMIN_MFA_REQUIRED = False
        APP_REQUIRE_EMAIL_VERIFICATION = False


@unittest.skipIf(IMPORT_ERROR is not None, f"Phase 5 runtime dependencies are not installed: {IMPORT_ERROR}")
class Phase5FunctionalRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(Phase5TestingConfig)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            category = Category(name="Electrical", slug="electrical", icon="fa-bolt", is_active=1)
            db.session.add(category); db.session.flush()
            service = Service(category_id=category.id, name="Electrician", slug="electrician", is_active=1)
            db.session.add(service); db.session.flush()
            customer = User(name="Customer", email="customer@example.com", password_hash="unused", role="customer", status="active", session_version=1)
            provider = User(name="Provider", email="provider@example.com", password_hash="unused", role="provider", status="active", session_version=1)
            db.session.add_all([customer, provider]); db.session.flush()
            db.session.add(ProviderProfile(user_id=provider.id, headline="Electrician", about="Experienced local electrician", service_area="Central", verification_status="verified"))
            db.session.add(ProviderService(provider_user_id=provider.id, service_id=service.id, title="Electrical repair", is_active=1))
            db.session.commit()
            self.category_id = int(category.id); self.service_id = int(service.id); self.customer_id = int(customer.id); self.provider_id = int(provider.id)

    def tearDown(self):
        with self.app.app_context():
            db.session.remove(); db.drop_all()

    def login_as(self, user_id: int) -> None:
        now = int(time.time())
        with self.client.session_transaction() as sess:
            sess.clear(); sess["user_id"] = user_id; sess["session_version"] = 1
            sess["_created_at"] = now; sess["_last_activity"] = now; sess["_rotated_at"] = now; sess["_nonce"] = "runtime-test"

    def test_customer_posts_requirement_and_provider_claims_then_accepts(self):
        self.login_as(self.customer_id)
        response = self.client.post("/post-requirement.php", data={
            "category_id": self.category_id, "service_id": self.service_id,
            "title": "Fix switchboard", "description": "Switchboard needs repair",
            "location_text": "Central", "budget_min": "500", "budget_max": "1500",
        })
        self.assertEqual(response.status_code, 303)
        with self.app.app_context():
            row = db.session.query(ServiceRequest).one()
            request_id = int(row.id)
            self.assertEqual(row.request_type, "requirement")
            self.assertEqual(db.session.query(RequestStatusHistory).filter_by(request_id=request_id, status="pending").count(), 1)

        self.login_as(self.provider_id)
        claim = self.client.post(f"/request-details.php?id={request_id}", data={"action": "claim", "id": request_id})
        self.assertEqual(claim.status_code, 303)
        accept = self.client.post(f"/request-details.php?id={request_id}", data={"action": "status", "status": "accepted", "id": request_id})
        self.assertEqual(accept.status_code, 303)
        with self.app.app_context():
            row = db.session.get(ServiceRequest, request_id)
            self.assertEqual(row.provider_id, self.provider_id)
            self.assertEqual(row.status, "accepted")

    def test_favorite_json_contract_and_completed_request_review_uniqueness(self):
        with self.app.app_context():
            row = ServiceRequest(customer_id=self.customer_id, provider_id=self.provider_id, category_id=self.category_id, service_id=self.service_id, request_type="direct", title="Repair", description="Repair request", location_text="Central", status="completed")
            db.session.add(row); db.session.commit(); request_id = int(row.id)
        self.login_as(self.customer_id)
        fav = self.client.post("/ajax/favorite.php", data={"target_user_id": self.provider_id})
        self.assertEqual(fav.status_code, 200); self.assertEqual(fav.get_json(), {"ok": True, "favorite": True})
        review = self.client.post("/reviews.php", data={"request_id": request_id, "rating": 5, "comment": "Great service"})
        self.assertEqual(review.status_code, 303)
        replay = self.client.post("/reviews.php", data={"request_id": request_id, "rating": 4, "comment": "Second review"})
        self.assertEqual(replay.status_code, 303)
        with self.app.app_context():
            self.assertEqual(db.session.query(Review).filter_by(request_id=request_id).count(), 1)

    def test_due_scheduled_subscription_promotes_once_and_applies_benefits_once(self):
        with self.app.app_context():
            plan = SubscriptionPlan(code="professional", name="Professional", audience="provider", price_monthly=Decimal("100.00"), billing_period_months=1, featured_days=7, lead_limit=3, is_active=1)
            db.session.add(plan); db.session.flush()
            sub = Subscription(user_id=self.provider_id, plan="professional", plan_id=plan.id, status="scheduled", starts_at=datetime.now() - timedelta(minutes=1), ends_at=datetime.now() + timedelta(days=30), price=Decimal("100.00"))
            db.session.add(sub); db.session.flush()
            db.session.add(FeaturedListing(user_id=self.provider_id, subscription_id=sub.id, status="pending", starts_at=datetime.now() - timedelta(minutes=1), ends_at=datetime.now() + timedelta(days=7)))
            db.session.commit(); sub_id = int(sub.id)

            first = current_subscription(self.provider_id); db.session.commit()
            self.assertIsNotNone(first); self.assertEqual(first.id, sub_id); self.assertEqual(first.status, "active")
            wallet = db.session.get(LeadWallet, self.provider_id); self.assertEqual(wallet.credits, 3)
            featured = db.session.query(FeaturedListing).filter_by(subscription_id=sub_id).one(); self.assertEqual(featured.status, "active")
            second = current_subscription(self.provider_id); db.session.commit()
            self.assertEqual(second.id, sub_id)
            self.assertEqual(db.session.get(LeadWallet, self.provider_id).credits, 3)


if __name__ == "__main__":
    unittest.main()
