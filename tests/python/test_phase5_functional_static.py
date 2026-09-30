from __future__ import annotations

import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parents[2]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(path: str, *needles: str) -> None:
    body = text(path)
    for needle in needles:
        assert needle in body, f"{path}: missing {needle!r}"


def python_route_paths() -> set[str]:
    found: set[str] = set()
    for path in (ROOT / "routes").glob("*.py"):
        body = path.read_text(encoding="utf-8")
        found.update(re.findall(r'@(?:bp|app)\.(?:get|post|route)\("([^\"]+)"', body))
    return found


def documented_legacy_paths() -> set[str]:
    body = text("docs/ROUTE_MAP.md")
    return set(re.findall(r'^\| `(/[^`]+\.php)` \|', body, flags=re.M))


def test_all_legacy_web_routes_have_python_compatibility_routes() -> None:
    documented = documented_legacy_paths()
    implemented = python_route_paths()
    missing = sorted(documented - implemented)
    assert len(documented) == 69, f"audit route count changed unexpectedly: {len(documented)}"
    assert not missing, f"missing Flask compatibility routes: {missing}"


def test_marketplace_workflow_rules_are_centralized() -> None:
    require(
        "routes/main.py",
        '"pending":["accepted","rejected"]',
        '"accepted":["in_progress","cancelled"]',
        '"in_progress":["completed","cancelled"]',
        ".with_for_update()",
        "Review.request_id == ServiceRequest.id",
    )
    require("services/marketplace_service.py", "create_notification", "rating_summary", "is_favorite")


def test_subscription_rollover_matches_legacy_locking_and_benefits() -> None:
    require(
        "services/marketplace_service.py",
        "_refresh_current_subscription_locked",
        "with_for_update()",
        'Subscription.status == "scheduled"',
        'listing.status = "active"',
        "wallet.credits = int(wallet.credits or 0) + int(plan.lead_limit or 0)",
        "scheduled.benefits_applied_at = now",
    )


def test_customer_provider_business_admin_surfaces_present() -> None:
    for route_file, needles in {
        "routes/customer.py": ("/customer/dashboard.php", "/customer/requests.php", "/post-requirement.php", "/request-service.php", "/favorites.php"),
        "routes/provider.py": ("/provider/dashboard.php", "/provider/profile.php", "/provider/services.php", "/provider/portfolio.php", "/provider/requests.php", "/provider/available-requirements.php", "/provider/subscription.php"),
        "routes/business.py": ("/business/dashboard.php", "/business/profile.php", "/business/services.php", "/business/requests.php", "/business/subscription.php"),
        "routes/admin.py": ("/admin/index.php", "/admin/users.php", "/admin/providers.php", "/admin/businesses.php", "/admin/categories.php", "/admin/services.php", "/admin/requests.php", "/admin/reviews.php", "/admin/reports.php", "/admin/advertisements.php", "/admin/subscriptions.php", "/admin/payments.php", "/admin/payment-detail.php", "/admin/payment-methods.php", "/admin/payment-method-edit.php"),
    }.items():
        require(route_file, *needles)


def test_ajax_favorite_contract_and_webhook_isolation() -> None:
    require("routes/api.py", "/ajax/favorite.php", "jsonify(ok=True", "favorite=False", "favorite=True")
    require("routes/webhooks.py", "/webhooks/razorpay.php", "@csrf.exempt", "request.get_data(cache=False, as_text=False)", "X-Razorpay-Signature")
    webhook_body = text("routes/webhooks.py")
    assert "@csrf.exempt" in webhook_body
    assert text("routes/api.py").count("@csrf.exempt") == 0, "browser favorite endpoint must stay CSRF-protected"


def test_billing_state_machine_and_reconciliation_worker_present() -> None:
    require(
        "services/billing_service.py",
        "create_checkout_intent",
        "create_payment_for_intent",
        "record_gateway_callback",
        "reconcile_razorpay",
        "mark_payment_failed",
        "mark_refund_state",
        "mark_disputed",
        "enqueue_reconciliation_job",
        "run_reconciliation_batch",
        "process_razorpay_webhook",
        "hmac.compare_digest",
    )
    require("scripts/payment_reconciliation_worker.py", "run_reconciliation_batch")


def test_sensitive_admin_payment_actions_keep_mfa_and_reauth_guards() -> None:
    body = text("routes/admin.py")
    detail_at = body.index('"/admin/payment-detail.php"')
    context = body[max(0, detail_at - 500): detail_at + 5000]
    assert "require_admin_mfa" in context or "admin_mfa" in context
    assert "require_recent_admin_reauth" in body


def test_all_rendered_templates_exist_and_parse() -> None:
    referenced: set[str] = set()
    for route in (ROOT / "routes").glob("*.py"):
        referenced.update(re.findall(r'render_template\("([^\"]+)"', route.read_text(encoding="utf-8")))
    missing = sorted(name for name in referenced if not (ROOT / "templates" / name).is_file())
    assert not missing, f"missing rendered templates: {missing}"

    env = Environment(loader=FileSystemLoader(str(ROOT / "templates")))
    templates = sorted(path.relative_to(ROOT / "templates").as_posix() for path in (ROOT / "templates").rglob("*.html"))
    assert len(templates) >= 60, f"expected migrated template surface, found only {len(templates)}"
    for name in templates:
        env.parse((ROOT / "templates" / name).read_text(encoding="utf-8"))


def test_existing_frontend_asset_contract_remains_in_use() -> None:
    require("templates/base.html", "assets/css/style.css", "assets/js/app.js")
    require("routes/main.py", "/uploads/<path:filename>", "send_from_directory")
    require("requirements.txt", "Pillow==")


def test_no_empty_phase5_route_modules() -> None:
    for name in ("main.py", "customer.py", "provider.py", "business.py", "admin.py", "billing.py", "api.py", "webhooks.py"):
        body = text(f"routes/{name}")
        assert "Blueprint(" in body, f"routes/{name} has no blueprint"
        assert "render_template" in body or "jsonify" in body or "redirect" in body, f"routes/{name} does not implement responses"


def test_legacy_route_methods_match_audited_contract() -> None:
    import ast

    implemented: dict[str, set[str]] = {}
    for path in (ROOT / "routes").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call) or not isinstance(dec.func, ast.Attribute) or not dec.args:
                    continue
                if dec.func.attr not in {"get", "post", "route"}:
                    continue
                first = dec.args[0]
                if not isinstance(first, ast.Constant) or not isinstance(first.value, str):
                    continue
                methods = {dec.func.attr.upper()} if dec.func.attr in {"get", "post"} else {"GET"}
                if dec.func.attr == "route":
                    for kw in dec.keywords:
                        if kw.arg == "methods" and isinstance(kw.value, (ast.List, ast.Tuple)):
                            methods = {item.value for item in kw.value.elts if isinstance(item, ast.Constant)}
                implemented.setdefault(first.value, set()).update(methods)

    expected: dict[str, set[str]] = {}
    for line in text("docs/ROUTE_MAP.md").splitlines():
        match = re.match(r'^\| `(/[^`]+\.php)` \| ([^|]+) \|', line)
        if match:
            expected[match.group(1)] = {part.strip() for part in match.group(2).split(",")}
    mismatches = {path: (methods, implemented.get(path, set())) for path, methods in expected.items() if methods != implemented.get(path, set())}
    assert not mismatches, f"legacy method contract mismatches: {mismatches}"


def test_protected_functional_routes_have_server_side_guards() -> None:
    protected = {
        "routes/customer.py": ["/customer/dashboard.php", "/customer/requests.php", "/post-requirement.php", "/request-service.php", "/favorites.php"],
        "routes/provider.py": ["/provider/dashboard.php", "/provider/profile.php", "/provider/services.php", "/provider/portfolio.php", "/provider/requests.php", "/provider/available-requirements.php", "/provider/subscription.php"],
        "routes/business.py": ["/business/dashboard.php", "/business/profile.php", "/business/services.php", "/business/requests.php", "/business/subscription.php"],
        "routes/billing.py": ["/billing/start.php", "/billing/payment-method.php", "/billing/select-method.php", "/billing/gateway.php", "/billing/gateway-return.php", "/billing/manual.php", "/billing/history.php", "/billing/cancel.php"],
        "routes/admin.py": ["/admin/index.php", "/admin/users.php", "/admin/providers.php", "/admin/businesses.php", "/admin/categories.php", "/admin/services.php", "/admin/requests.php", "/admin/reviews.php", "/admin/reports.php", "/admin/advertisements.php", "/admin/subscriptions.php", "/admin/payments.php", "/admin/payment-detail.php", "/admin/payment-methods.php", "/admin/payment-method-edit.php"],
        "routes/api.py": ["/ajax/favorite.php"],
    }
    for route_file, paths in protected.items():
        body = text(route_file)
        for path in paths:
            pattern = re.compile(r'@bp\.(?:get|post|route)\("' + re.escape(path) + r'"[^\n]*\)\s*\n@require_(?:roles|login)')
            assert pattern.search(body), f"{path} lacks server-side auth guard"
    main = text("routes/main.py")
    for path in ("/notifications.php", "/reviews.php", "/report.php", "/request-details.php"):
        pattern = re.compile(r'@bp\.(?:get|post|route)\("' + re.escape(path) + r'"[^\n]*\)\s*\n@require_login')
        assert pattern.search(main), f"{path} lacks login guard"


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"PASS {len(tests)}/{len(tests)} Phase 5 functional static checks")
