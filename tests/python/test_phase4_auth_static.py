from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(path: str, *needles: str) -> None:
    body = text(path)
    for needle in needles:
        assert needle in body, f"{path}: missing {needle!r}"


def test_auth_routes_present() -> None:
    require(
        "routes/auth.py",
        '/auth/login.php', '/login.php', '/auth/register.php', '/register.php',
        '/auth/logout.php', '/logout.php', '/auth/forgot-password.php',
        '/auth/reset-password.php', '/auth/resend-verification.php', '/auth/verify-email.php',
    )


def test_login_security_parity() -> None:
    require(
        "routes/auth.py",
        "_DUMMY_HASH", "login_rate_failure", "login_rate_success", "password_needs_rehash",
        'status == "blocked"', 'status == "pending"', "establish_session", "admin_mfa_needed",
    )
    require("services/auth_service.py", "bcrypt.checkpw", 'candidate.startswith(b"$2y$")', "bcrypt.gensalt(rounds=12)")


def test_registration_and_role_profiles() -> None:
    require("services/auth_service.py", 'ALLOWED_REGISTRATION_ROLES = {"customer", "provider", "business"}', "ProviderProfile", "BusinessProfile", "account_registered")
    require("routes/auth.py", 'APP_REQUIRE_EMAIL_VERIFICATION', 'create_auth_token(user.id, "email_verify", 86400)')


def test_reset_verification_tokens_are_hashed_and_single_use() -> None:
    require("services/auth_service.py", "secrets.token_hex(32)", "hashlib.sha256(validator.encode()).hexdigest()", "used_at.is_(None)", "expires_at > datetime.now()")
    require("routes/auth.py", "session_version = int(user.session_version or 1) + 1", "record.used_at = datetime.now()")


def test_rate_limit_buckets_match_php_design() -> None:
    require("services/auth_service.py", 'app_hmac(email, "login-email")', 'app_hmac(client_ip_hash(), "login-ip")', '"auth-action-email"', '"auth-action-ip"', ".with_for_update()")


def test_session_lifecycle_and_role_guards() -> None:
    require("utils/auth.py", "SESSION_IDLE_TIMEOUT", "SESSION_ABSOLUTE_TIMEOUT", "SESSION_ROTATE_INTERVAL", 'session["_nonce"] = secrets.token_hex(16)', "session_version", "require_roles")
    require("utils/security.py", 'response.headers["Cache-Control"] = "private, no-store, max-age=0"')


def test_admin_mfa_and_reauth() -> None:
    require("routes/admin.py", '/admin/mfa.php', '/admin/reauth.php', "verify_totp", "last_used_step", "admin_reauth_at", "pending_mfa_secret_box")
    require("services/auth_service.py", "sodium_secretbox", "aes-256-gcm", "SecretBox", "AESGCM", "candidate <= last_used_step")


def test_csrf_and_post_logout() -> None:
    require("routes/errors.py", "CSRFError", "419")
    body = text("routes/auth.py")
    assert re.search(r'@bp\.route\("/auth/logout\.php", methods=\["POST"\]\)', body)
    assert re.search(r'@bp\.route\("/logout\.php", methods=\["POST"\]\)', body)
    for page in ["auth/login.html", "auth/register.html", "auth/forgot_password.html", "auth/reset_password.html", "auth/resend_verification.html", "admin/mfa.html", "admin/reauth.html"]:
        require(f"templates/{page}", 'name="csrf_token"')


def test_frontend_assets_still_used() -> None:
    require("templates/base.html", "assets/css/style.css", "assets/js/app.js", "bootstrap@5.3.3", "font-awesome")


def test_runtime_dependencies_declared() -> None:
    req = text("requirements.txt")
    for package in ("Flask==", "Flask-SQLAlchemy==", "Flask-WTF==", "psycopg[binary]==", "bcrypt==", "PyNaCl==", "cryptography=="):
        assert package in req, f"missing dependency {package}"


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"PASS {len(tests)}/{len(tests)} Phase 4 auth static checks")
