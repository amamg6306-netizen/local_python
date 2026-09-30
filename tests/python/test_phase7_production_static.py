from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(path: str, *needles: str) -> None:
    body = text(path)
    for needle in needles:
        assert needle in body, f"{path}: missing {needle!r}"


def test_render_blueprint_uses_native_python_and_persistent_upload_disk() -> None:
    body = text("render.yaml")
    require("render.yaml", "runtime: python", "gunicorn app:app --bind 0.0.0.0:$PORT", "healthCheckPath: /health")
    require("render.yaml", "disk:", "mountPath: /var/data/localconnect/uploads", "sizeGB: 1")
    assert "runtime: docker" not in body.lower()
    assert "dockerfile" not in body.lower()


def test_production_config_requires_durable_storage_and_safe_limits() -> None:
    require(
        "config/settings.py",
        'UPLOAD_STORAGE_BACKEND =',
        'UPLOAD_STORAGE_ROOT =',
        'UPLOAD_DISK_REQUIRED =',
        'UPLOAD_MAX_FILE_BYTES =',
        'MAX_CONTENT_LENGTH =',
        'MAX_FORM_MEMORY_SIZE =',
        'MAX_FORM_PARTS =',
        'TRUSTED_HOSTS =',
    )
    require("config/settings.py", "UPLOAD_STORAGE_ROOT is required when UPLOAD_DISK_REQUIRED is enabled.")
    require("config/settings.py", "SMTP_HOST is required when APP_MAIL_DRIVER=smtp.")


def test_storage_service_is_bounded_reencoded_and_path_restricted() -> None:
    require(
        "services/storage_service.py",
        '_ALLOWED_FOLDERS = {"profiles", "businesses", "portfolio"}',
        'stream.read(64 * 1024)',
        'if total > max_bytes:',
        'ImageOps.exif_transpose(image)',
        'UPLOAD_REQUIRE_REENCODE',
        'os.replace(tmp, output)',
        'os.chmod(output, 0o640)',
        '{32,40}',
    )
    body = text("services/storage_service.py")
    assert "secure_filename(file.filename" not in body, "client filename must never become storage filename"


def test_legacy_database_upload_paths_are_preserved() -> None:
    require("services/marketplace_service.py", "Compatibility wrapper preserving the legacy uploads/... database path contract.")
    require("services/storage_service.py", 'return f"uploads/{normalized_folder}/{filename}"')


def test_public_upload_route_uses_configured_root_and_managed_path_validation() -> None:
    require(
        "routes/main.py",
        'resolve_managed_upload(f"uploads/{filename}")',
        "upload_storage_root()",
        'response.headers["Cache-Control"]',
        'response.headers["CDN-Cache-Control"]',
        'abort(404)',
    )


def test_application_probes_storage_before_serving_in_production() -> None:
    require("app.py", "ensure_storage_ready", "writable_probe=app.config[\"APP_ENV\"] == \"production\"")


def test_logs_redact_secrets_and_include_render_trace_ids() -> None:
    require("utils/logging.py", "[REDACTED]", 'request.headers.get("Rndr-Id")', 'request.headers.get("CF-Ray")')
    require("utils/observability.py", "Server-Timing", "slow_request", "SLOW_REQUEST_MS")


def test_security_and_request_failure_guards_remain_present() -> None:
    require("utils/security.py", "Content-Security-Policy", "Strict-Transport-Security", "X-Content-Type-Options", "Permissions-Policy")
    require("routes/errors.py", "@app.errorhandler(413)", "The uploaded request is too large.")


def test_legacy_upload_sync_is_idempotent_and_non_overwriting() -> None:
    path = ROOT / "scripts" / "sync_uploads_to_storage.py"
    spec = importlib.util.spec_from_file_location("sync_uploads_to_storage", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        source = root / "source"
        target = root / "target"
        image = source / "profiles" / ("a" * 32 + ".jpg")
        image.parent.mkdir(parents=True)
        image.write_bytes(b"legacy-image")
        first = module.sync(source, target)
        second = module.sync(source, target)
        assert first == (1, 0, 0)
        assert second == (0, 1, 0)
        image.write_bytes(b"different")
        third = module.sync(source, target)
        assert third == (0, 0, 1)
        assert (target / "profiles" / image.name).read_bytes() == b"legacy-image"


def test_environment_template_contains_phase7_production_controls() -> None:
    require(
        ".env.example",
        "UPLOAD_STORAGE_BACKEND=filesystem",
        "UPLOAD_STORAGE_ROOT=/var/data/localconnect/uploads",
        "UPLOAD_DISK_REQUIRED=true",
        "TRUSTED_HOSTS=example.onrender.com",
        "MAX_REQUEST_BYTES=8388608",
        "SLOW_REQUEST_MS=1500",
    )


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"PASS {len(tests)}/{len(tests)} Phase 7 production static checks")
