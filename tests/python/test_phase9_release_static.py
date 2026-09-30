from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_render_is_native_python_no_docker():
    y = read("render.yaml")
    assert "runtime: python" in y
    assert "runtime: docker" not in y.lower()
    assert "buildCommand: pip install -r requirements.txt" in y
    assert "startCommand: gunicorn app:app --bind 0.0.0.0:$PORT" in y
    assert "healthCheckPath: /health" in y
    assert not any(ROOT.glob("Dockerfile*"))


def test_render_has_predeploy_release_gates():
    y = read("render.yaml")
    assert "preDeployCommand: python scripts/check_config.py && python scripts/check_db_schema.py" in y


def test_render_declares_persistent_upload_disk():
    y = read("render.yaml")
    assert "mountPath: /var/data/localconnect/uploads" in y
    assert "UPLOAD_STORAGE_ROOT" in y
    assert "/var/data/localconnect/uploads" in y


def test_render_declares_payment_secrets_without_values():
    y = read("render.yaml")
    for key in (
        "PAYMENT_RAZORPAY_KEY_ID",
        "PAYMENT_RAZORPAY_KEY_SECRET",
        "PAYMENT_RAZORPAY_WEBHOOK_SECRET",
        "PAYMENT_RAZORPAY_WEBHOOK_IP_ALLOWLIST",
    ):
        marker = f"- key: {key}"
        assert marker in y
        start = y.index(marker)
        next_key = y.find("      - key:", start + len(marker))
        block = y[start:] if next_key == -1 else y[start:next_key]
        assert "sync: false" in block
    assert 'PAYMENT_ALLOW_LIVE\n        value: "false"' in y


def test_health_checks_primary_database_without_leaking_details():
    h = read("routes/health.py")
    assert 'text("SELECT 1")' in h
    assert 'jsonify(status="ok")' in h
    assert 'jsonify(status="error")' in h
    assert "503" in h
    assert "str(exc)" not in h


def test_readme_is_python_first():
    r = read("README.md")
    assert "Python/Flask" in r
    assert "No XAMPP, WAMP, Apache, PHP or Docker is required" in r
    assert "gunicorn app:app" in r
    assert "scripts/check_db_schema.py" in r


def test_no_obsolete_server_runtime_configs():
    assert not (ROOT / "deploy" / "apache").exists()
    assert not (ROOT / "deploy" / "php").exists()


def test_no_committed_runtime_secret_file():
    forbidden = [ROOT / ".env", ROOT / "config" / ".env"]
    assert not any(p.exists() for p in forbidden)


def test_python_version_pinned_consistently():
    assert read(".python-version").strip() == "3.13.15"
    assert "PYTHON_VERSION\n        value: 3.13.15" in read("render.yaml")
    assert "PYTHON_VERSION=3.13.15" in read(".env.example")
