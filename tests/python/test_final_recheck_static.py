from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_sqlalchemy_minor_line_is_pinned_for_reproducible_deploys():
    requirements = read("requirements.txt").splitlines()
    assert "Flask-SQLAlchemy==3.1.1" in requirements
    assert "SQLAlchemy==2.0.54" in requirements
    assert "greenlet==3.5.6" in requirements
    assert "Werkzeug==3.1.9" in requirements
    assert "WTForms==3.2.2" in requirements
    assert "cryptography==50.0.1" in requirements


def test_razorpay_response_body_is_bounded_before_json_decode():
    source = read("services/billing_service.py")
    assert "max_response_bytes = 1_048_576" in source
    assert "response.read(max_response_bytes + 1)" in source
    assert "Payment gateway response exceeded the safe size limit." in source


def test_contact_form_uses_shared_email_validator():
    source = read("routes/main.py")
    assert "from services.auth_service import clean_text, is_valid_email" in source
    assert "if not is_valid_email(email) or len(message) < 10:" in source


def test_external_static_assets_have_integrity_metadata():
    for rel in ("templates/base.html", "templates/errors/base.html"):
        template = read(rel)
        assert "bootstrap@5.3.3/dist/css/bootstrap.min.css" in template
        assert "sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" in template
        assert "bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js" in template
        assert "sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz" in template
        assert "font-awesome/6.5.2/css/all.min.css" in template
        assert "sha512-SnH5WK+bZxgPHs44uWIX+LLJAJ9/2PkPKZ5QiAj6Ta86w+fsb2TkcmfRyVX3pBnMFcV7oQPJkl9QevSCWr3W6A==" in template
        assert template.count('crossorigin="anonymous"') >= 3


def test_render_schedules_bounded_payment_reconciliation_worker():
    render = read("render.yaml")
    assert "type: cron" in render
    assert "name: localconnect-payment-reconciliation" in render
    assert "schedule: '*/5 * * * *'" in render
    assert "startCommand: python scripts/payment_reconciliation_worker.py --limit=20" in render
    assert "UPLOAD_STORAGE_ROOT\n        value: /tmp/localconnect/uploads" in render
    assert "UPLOAD_DISK_REQUIRED\n        value: \"false\"" in render
    assert "envVarKey: DATABASE_URL" in render


def test_runbook_uses_python_reconciliation_worker():
    runbook = read("docs/PERFORMANCE_MEMORY_RUNBOOK.md")
    assert "python scripts/payment_reconciliation_worker.py --limit=20" in runbook
    assert "php tools/payment_reconciliation_worker.php" not in runbook


def test_subscription_expiry_uses_bulk_update_instead_of_materializing_rows():
    source = read("services/marketplace_service.py")
    assert "from sqlalchemy import func, select, update" in source
    assert "update(Subscription)" in source
    assert '.values(status="expired")' in source
    expiry_region = source[source.index("def _refresh_current_subscription_locked"):source.index("def current_subscription")]
    assert "expired = db.session.scalars" not in expiry_region
