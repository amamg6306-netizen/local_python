from __future__ import annotations

import unittest
from datetime import datetime

IMPORT_ERROR = None
try:
    from app import create_app
    from config.settings import TestingConfig
    from extensions import db
    from models.core import User
    from models.marketplace import ProviderProfile
    from services.auth_service import (
        create_auth_token,
        decrypt_sensitive,
        encrypt_sensitive,
        password_hash,
        password_verify,
        totp_code,
    )
except ModuleNotFoundError as exc:  # constrained audit environments may not have pip access
    IMPORT_ERROR = exc


if IMPORT_ERROR is None:
    class AuthTestingConfig(TestingConfig):
        APP_REQUIRE_EMAIL_VERIFICATION = False
        APP_ADMIN_MFA_REQUIRED = True
        APP_MAIL_DRIVER = "log"
        APP_MAIL_FROM = "no-reply@example.com"
        SESSION_IDLE_TIMEOUT = 1800
        SESSION_ABSOLUTE_TIMEOUT = 28800
        SESSION_ROTATE_INTERVAL = 900
else:
    class AuthTestingConfig:
        pass


class Phase4AuthRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if IMPORT_ERROR is not None:
            raise unittest.SkipTest(f"Phase 4 runtime dependencies are not installed: {IMPORT_ERROR}")

    def setUp(self):
        self.app = create_app(AuthTestingConfig)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def add_user(self, *, email="user@example.com", password="correct horse battery staple", role="customer", status="active") -> int:
        with self.app.app_context():
            user = User(
                name="Test User",
                email=email,
                password_hash=password_hash(password),
                role=role,
                status=status,
                email_verified_at=datetime.now() if status == "active" else None,
                session_version=1,
            )
            db.session.add(user)
            db.session.commit()
            return int(user.id)

    def test_php_bcrypt_prefix_is_accepted(self):
        encoded = password_hash("correct horse battery staple")
        php_style = "$2y$" + encoded[4:]
        self.assertTrue(password_verify("correct horse battery staple", php_style))
        self.assertFalse(password_verify("wrong password", php_style))

    def test_registration_creates_provider_profile(self):
        response = self.client.post(
            "/auth/register.php",
            data={
                "role": "provider",
                "name": "Provider One",
                "email": "provider@example.com",
                "phone": "+91 9876543210",
                "city": "Lucknow",
                "state": "Uttar Pradesh",
                "password": "correct horse battery staple",
                "confirm_password": "correct horse battery staple",
            },
        )
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["Location"], "/provider/dashboard.php")
        with self.app.app_context():
            user = db.session.query(User).filter_by(email="provider@example.com").one()
            self.assertEqual(user.role, "provider")
            self.assertEqual(user.status, "active")
            self.assertIsNotNone(db.session.query(ProviderProfile).filter_by(user_id=user.id).one_or_none())

    def test_login_invalid_blocked_success_and_logout_method(self):
        self.add_user()
        invalid = self.client.post("/auth/login.php", data={"email": "user@example.com", "password": "wrong"})
        self.assertEqual(invalid.status_code, 200)
        self.assertIn(b"Invalid email or password.", invalid.data)

        success = self.client.post("/auth/login.php", data={"email": "user@example.com", "password": "correct horse battery staple"})
        self.assertEqual(success.status_code, 303)
        self.assertEqual(success.headers["Location"], "/customer/dashboard.php")
        self.assertEqual(self.client.get("/auth/logout.php").status_code, 405)
        self.assertEqual(self.client.post("/auth/logout.php").status_code, 303)

        with self.app.app_context():
            user = db.session.query(User).filter_by(email="user@example.com").one()
            user.status = "blocked"
            db.session.commit()
        blocked = self.client.post("/auth/login.php", data={"email": "user@example.com", "password": "correct horse battery staple"})
        self.assertIn(b"account has been blocked", blocked.data)

    def test_password_reset_invalidates_session_version_and_token(self):
        user_id = self.add_user()
        with self.app.test_request_context("/auth/forgot-password.php", environ_base={"REMOTE_ADDR": "127.0.0.1"}):
            token = create_auth_token(user_id, "password_reset", 3600)
        response = self.client.post(
            "/auth/reset-password.php",
            data={
                "selector": token["selector"],
                "token": token["token"],
                "password": "new correct horse battery staple",
                "confirm_password": "new correct horse battery staple",
            },
        )
        self.assertEqual(response.status_code, 303)
        with self.app.app_context():
            user = db.session.get(User, user_id)
            self.assertEqual(user.session_version, 2)
            self.assertTrue(password_verify("new correct horse battery staple", user.password_hash))
        replay = self.client.post(
            "/auth/reset-password.php",
            data={"selector": token["selector"], "token": token["token"], "password": "another long password here", "confirm_password": "another long password here"},
        )
        self.assertIn(b"invalid or expired", replay.data)

    def test_admin_mfa_setup_and_replay_protection(self):
        self.add_user(email="admin@example.com", role="admin")
        login = self.client.post("/auth/login.php", data={"email": "admin@example.com", "password": "correct horse battery staple"})
        self.assertEqual(login.status_code, 303)
        self.assertEqual(login.headers["Location"], "/admin/mfa.php")
        setup = self.client.get("/admin/mfa.php")
        self.assertEqual(setup.status_code, 200)
        with self.client.session_transaction() as sess:
            pending = dict(sess["pending_mfa_secret_box"])
        with self.app.app_context():
            secret = decrypt_sensitive(pending["ciphertext"], pending["nonce"], pending["alg"])
        code = totp_code(secret)
        enable = self.client.post("/admin/mfa.php", data={"action": "enable", "password": "correct horse battery staple", "code": code})
        self.assertEqual(enable.status_code, 303)
        # The exact same time-step code cannot be accepted again.
        replay = self.client.post("/admin/mfa.php", data={"action": "verify", "code": code})
        self.assertIn(b"already-used", replay.data)

    def test_sensitive_secret_round_trip_for_legacy_algorithms(self):
        with self.app.app_context():
            for algorithm in ("sodium_secretbox", "aes-256-gcm"):
                encrypted = encrypt_sensitive("JBSWY3DPEHPK3PXP", algorithm)
                self.assertEqual(decrypt_sensitive(encrypted["ciphertext"], encrypted["nonce"], encrypted["alg"]), "JBSWY3DPEHPK3PXP")

    def test_role_guard_denies_non_admin(self):
        self.add_user()
        self.client.post("/auth/login.php", data={"email": "user@example.com", "password": "correct horse battery staple"})
        self.assertEqual(self.client.get("/admin/mfa.php").status_code, 403)


if __name__ == "__main__":
    unittest.main()
