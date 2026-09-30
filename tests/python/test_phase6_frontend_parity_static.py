from __future__ import annotations

import ast
import re
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlsplit

from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parents[2]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def route_paths() -> set[str]:
    paths: set[str] = set()
    for file in (ROOT / "routes").glob("*.py"):
        tree = ast.parse(file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call) or not isinstance(dec.func, ast.Attribute) or not dec.args:
                    continue
                if dec.func.attr not in {"get", "post", "route"}:
                    continue
                arg = dec.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    paths.add(arg.value)
    return paths


def static_tokens(body: str, *, php: bool) -> list[str]:
    if php:
        body = re.sub(r"<\?(?:php|=).*?\?>", " ", body, flags=re.S | re.I)
    else:
        body = re.sub(r"{[%{#].*?[}%#]}", " ", body, flags=re.S)
    return re.findall(r"[a-z0-9_-]+", body.lower())


def similarity(php_path: str, template_path: str) -> tuple[float, float]:
    old = static_tokens(text(php_path), php=True)
    new = static_tokens(text(template_path), php=False)
    a, b = set(old), set(new)
    jaccard = len(a & b) / len(a | b) if a | b else 1.0
    sequence = SequenceMatcher(None, old, new, autojunk=False).ratio()
    return jaccard, sequence


def test_all_jinja_templates_parse_and_dependencies_exist() -> None:
    env = Environment(loader=FileSystemLoader(str(ROOT / "templates")))
    templates = sorted((ROOT / "templates").rglob("*.html"))
    assert len(templates) >= 62
    for path in templates:
        source = path.read_text(encoding="utf-8")
        env.parse(source)
        for match in re.finditer(r"{%\s*(?:extends|include)\s+['\"]([^'\"]+)['\"]", source):
            assert (ROOT / "templates" / match.group(1)).is_file(), f"{path}: missing template dependency {match.group(1)}"


def test_critical_pages_keep_legacy_static_markup_vocabulary() -> None:
    pairs = {
        "index.php": "templates/main/index.html",
        "categories.php": "templates/main/categories.html",
        "search.php": "templates/main/search.html",
        "provider.php": "templates/main/provider_detail.html",
        "business.php": "templates/main/business_detail.html",
        "contact.php": "templates/main/contact.html",
        "reviews.php": "templates/main/reviews.html",
        "report.php": "templates/main/report.html",
        "request-details.php": "templates/main/request_details.html",
        "customer/dashboard.php": "templates/customer/dashboard.html",
        "customer/requests.php": "templates/customer/requests.html",
        "post-requirement.php": "templates/customer/post_requirement.html",
        "request-service.php": "templates/customer/request_service.html",
        "favorites.php": "templates/customer/favorites.html",
        "provider/dashboard.php": "templates/provider/dashboard.html",
        "provider/profile.php": "templates/provider/profile.html",
        "provider/services.php": "templates/provider/services.html",
        "provider/portfolio.php": "templates/provider/portfolio.html",
        "provider/requests.php": "templates/provider/requests.html",
        "provider/available-requirements.php": "templates/provider/available_requirements.html",
        "provider/subscription.php": "templates/provider/subscription.html",
        "business/dashboard.php": "templates/business/dashboard.html",
        "business/profile.php": "templates/business/profile.html",
        "business/services.php": "templates/business/services.html",
        "business/subscription.php": "templates/business/subscription.html",
        "admin/users.php": "templates/admin/users.html",
        "admin/providers.php": "templates/admin/providers.html",
        "admin/businesses.php": "templates/admin/businesses.html",
        "admin/categories.php": "templates/admin/categories.html",
        "admin/services.php": "templates/admin/services.html",
        "admin/requests.php": "templates/admin/requests.html",
        "admin/reviews.php": "templates/admin/reviews.html",
        "admin/reports.php": "templates/admin/reports.html",
        "admin/advertisements.php": "templates/admin/advertisements.html",
        "admin/subscriptions.php": "templates/admin/subscriptions.html",
        "admin/payments.php": "templates/admin/payments.html",
        "admin/payment-detail.php": "templates/admin/payment_detail.html",
        "admin/payment-methods.php": "templates/admin/payment_methods.html",
        "admin/payment-method-edit.php": "templates/admin/payment_method_edit.html",
        "billing/payment-method.php": "templates/billing/payment_method.html",
        "billing/gateway.php": "templates/billing/gateway.html",
        "billing/manual.php": "templates/billing/manual.html",
        "billing/history.php": "templates/billing/history.html",
    }
    low: dict[str, tuple[float, float]] = {}
    for old, new in pairs.items():
        jaccard, sequence = similarity(old, new)
        if jaccard < 0.82 or sequence < 0.88:
            low[old] = (round(jaccard, 3), round(sequence, 3))
    assert not low, f"frontend parity drift detected: {low}"


def test_post_forms_have_csrf_tokens() -> None:
    missing: list[str] = []
    pattern = re.compile(r"<form\b[^>]*method=['\"]post['\"][^>]*>(.*?)</form>", re.I | re.S)
    for path in (ROOT / "templates").rglob("*.html"):
        source = path.read_text(encoding="utf-8")
        for form in pattern.finditer(source):
            if "csrf_token" not in form.group(1):
                missing.append(path.relative_to(ROOT).as_posix())
    assert not missing, f"POST forms missing CSRF: {sorted(set(missing))}"


def test_all_literal_php_template_links_resolve_to_flask_routes() -> None:
    implemented = route_paths()
    missing: set[str] = set()
    for path in (ROOT / "templates").rglob("*.html"):
        source = path.read_text(encoding="utf-8")
        for raw in re.findall(r"lc_url\(['\"]([^'\"]+\.php[^'\"]*)['\"]\)", source):
            route = "/" + urlsplit(raw).path.lstrip("/")
            if route not in implemented:
                missing.add(route)
    assert not missing, f"template links without Flask compatibility routes: {sorted(missing)}"


def test_local_static_asset_references_exist() -> None:
    missing: set[str] = set()
    for path in (ROOT / "templates").rglob("*.html"):
        source = path.read_text(encoding="utf-8")
        for ref in re.findall(r"(?:src|href)=['\"](?:{{\s*lc_url\(['\"])?(assets/[^'\"?) }]+)", source):
            if not (ROOT / ref).is_file():
                missing.add(ref)
    assert not missing, f"missing local static assets: {sorted(missing)}"
    base = text("templates/base.html")
    assert "assets/css/style.css" in base and "assets/js/app.js" in base


def test_ajax_favorite_keeps_legacy_url_and_json_contract() -> None:
    js = text("assets/js/app.js")
    assert "ajax/favorite.php" in js
    api = text("routes/api.py")
    assert '"/ajax/favorite.php"' in api
    for fragment in ("favorite=False", "favorite=True", "jsonify(ok=True"):
        assert fragment in api


def test_pagination_preserves_active_filters() -> None:
    app = text("app.py")
    partial = text("templates/partials/pagination.html")
    assert "request.args.to_dict(flat=False)" in app
    assert 'args["page"]' in app
    assert "urlencode(args, doseq=True)" in app
    assert "page_url(" in partial


def test_business_specific_surfaces_do_not_leak_provider_copy() -> None:
    services = text("templates/business/services.html")
    subscription = text("templates/business/subscription.html")
    provider_routes = text("routes/provider.py")
    assert "Add the services your business offers." in services
    assert "Only business-eligible plans are shown." in subscription
    assert '"business/services.html" if role == "business"' in provider_routes
    assert '"business/subscription.html" if role == "business"' in provider_routes


def test_frontend_library_contract_is_preserved() -> None:
    base = text("templates/base.html")
    for fragment in ("bootstrap@5.3.3", "font-awesome", "assets/css/style.css", "assets/js/app.js"):
        assert fragment in base
    css = text("assets/css/style.css")
    for klass in (".soft-card", ".category-card", ".service-row", ".request-status"):
        assert klass in css


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"PASS {len(tests)}/{len(tests)} Phase 6 frontend parity static checks")
