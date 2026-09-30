from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(path: str, *needles: str) -> None:
    body = text(path)
    for needle in needles:
        assert needle in body, f"{path}: missing {needle!r}"


def test_render_python_runtime_is_pinned() -> None:
    require(".python-version", "3.13.15")
    require("render.yaml", "PYTHON_VERSION", "value: 3.13.15")


def test_security_pinned_dependencies_are_updated() -> None:
    require(
        "requirements.txt",
        "Flask==3.1.3",
        "Flask-WTF==1.3.0",
        "cryptography==50.0.1",
        "gunicorn==26.2.0",
        "python-dotenv==1.2.3",
        "bcrypt==4.3.0",
        "PyNaCl==1.6.2",
        "Pillow==12.3.0",
    )


def test_new_passwords_do_not_rely_on_bcrypt_truncation() -> None:
    require(
        "services/auth_service.py",
        "def validate_new_password",
        "byte_length > 72",
        "Password is too long. Use at most 72 UTF-8 bytes.",
    )
    require("routes/auth.py", "validate_new_password(password)")


def test_upload_decoder_is_allowlisted_and_decompression_bomb_guarded() -> None:
    require(
        "services/storage_service.py",
        '_IMAGE_OPEN_FORMATS = tuple(_IMAGE_FORMATS)',
        "formats=_IMAGE_OPEN_FORMATS",
        "Image.DecompressionBombWarning",
        "check.width * check.height > max_pixels",
    )


def test_proxy_client_ip_uses_trusted_end_of_forwarding_chain() -> None:
    require(
        "services/auth_service.py",
        'TRUSTED_PROXY_HOPS',
        "return chain[max(0, len(chain) - hops)]",
    )
    require(
        "utils/security.py",
        "trusted_hops",
        "index = max(0, len(values) - self.trusted_hops)",
    )
    require("render.yaml", "TRUSTED_PROXY_HOPS", "value: \"1\"")


def test_production_database_url_fails_closed_to_mysql_pymysql() -> None:
    require(
        "config/settings.py",
        'urlsplit(normalized).scheme.lower() != "mysql+pymysql"',
        "DATABASE_URL must use MySQL/MariaDB via the mysql+pymysql driver in production.",
    )


def test_webhook_ip_allowlist_uses_canonical_client_ip() -> None:
    require(
        "services/billing_service.py",
        "from services.auth_service import clean_text, client_ip, log_activity, security_log",
        "if allowed and client_ip() not in allowed:",
    )


def test_payment_paid_and_entitlement_are_atomic() -> None:
    body = text("services/billing_service.py")
    mark_start = body.index("def mark_payment_paid")
    mark_end = body.index("\ndef ", mark_start + 10)
    mark = body[mark_start:mark_end]
    assert "activate_entitlement" in mark
    before_activation = mark.split("activate_entitlement", 1)[0]
    assert "db.session.commit()" not in before_activation, "paid state must not commit before entitlement activation"

    manual_start = body.index("def verify_manual_payment")
    manual_end = body.index("\ndef ", manual_start + 10)
    manual = body[manual_start:manual_end]
    assert "activate_entitlement" in manual


def test_mass_state_updates_do_not_materialize_unbounded_rows() -> None:
    require("routes/main.py", "update(Notification)", ".values(is_read=1)")
    require("services/billing_service.py", "update(CheckoutIntent)", '.values(status="expired")')
    require(
        "services/billing_service.py",
        "update(PaymentReconciliationJob)",
        'last_error="Recovered stale processing lease."',
        '.values(status="dead", locked_at=None)',
    )


def test_no_common_unsafe_execution_primitives_in_application_code() -> None:
    paths = list((ROOT / "routes").glob("*.py")) + list((ROOT / "services").glob("*.py")) + list((ROOT / "utils").glob("*.py"))
    joined = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    for needle in ("eval(", "exec(", "pickle.loads", "shell=True"):
        assert needle not in joined, f"unsafe primitive found: {needle}"


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"PASS {len(tests)}/{len(tests)} pre-Phase-8 recheck static checks")
