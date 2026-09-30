from __future__ import annotations

import ast
import builtins
import re
import unittest
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, meta

ROOT = Path(__file__).resolve().parents[2]


def _route_contract() -> dict[str, set[str]]:
    routes: dict[str, set[str]] = {}
    for path in (ROOT / "routes").glob("*.py"):
        tree = ast.parse(path.read_text())
        for fn in (n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))):
            for dec in fn.decorator_list:
                if not (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)):
                    continue
                if not (isinstance(dec.func.value, ast.Name) and dec.func.value.id == "bp"):
                    continue
                if not dec.args or not isinstance(dec.args[0], ast.Constant) or not isinstance(dec.args[0].value, str):
                    continue
                route = dec.args[0].value
                methods: set[str] = set()
                if dec.func.attr in {"get", "post", "put", "patch", "delete"}:
                    methods.add(dec.func.attr.upper())
                elif dec.func.attr == "route":
                    methods.add("GET")
                    for kw in dec.keywords:
                        if kw.arg == "methods" and isinstance(kw.value, (ast.List, ast.Tuple)):
                            methods = {str(item.value).upper() for item in kw.value.elts if isinstance(item, ast.Constant)}
                routes.setdefault(route, set()).update(methods)
    return routes


class Phase8VerificationStaticTests(unittest.TestCase):
    def test_python_model_attribute_references_exist(self):
        inherited = {"id", "created_at", "updated_at", "__table__"}
        model_fields: dict[str, set[str]] = {}
        for path in (ROOT / "models").glob("*.py"):
            if path.name == "__init__.py":
                continue
            tree = ast.parse(path.read_text())
            for node in tree.body:
                if not isinstance(node, ast.ClassDef):
                    continue
                fields = set(inherited)
                for child in node.body:
                    if isinstance(child, ast.Assign):
                        for target in child.targets:
                            if isinstance(target, ast.Name):
                                fields.add(target.id)
                    elif isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                        fields.add(child.target.id)
                    elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        fields.add(child.name)
                model_fields[node.name] = fields
        unknown = []
        for folder in ("routes", "services", "utils"):
            for path in (ROOT / folder).glob("*.py"):
                tree = ast.parse(path.read_text())
                for node in ast.walk(tree):
                    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in model_fields:
                        if node.attr not in model_fields[node.value.id]:
                            unknown.append((path.as_posix(), node.lineno, node.value.id, node.attr))
        self.assertEqual(unknown, [])

    def test_template_context_contracts_have_no_missing_direct_variables(self):
        env = Environment(loader=FileSystemLoader(str(ROOT / "templates")))
        globals_ = {
            "request", "session", "g", "url_for", "get_flashed_messages", "config",
            "csrf_token", "lc_url", "csp_nonce", "dashboard_url", "nav_user",
            "nav_notification_count", "current_year", "page_url", "range", "dict",
            "cycler", "joiner", "namespace", "lipsum",
        }
        failures = []
        for source_path in [ROOT / "app.py", *(ROOT / "routes").glob("*.py")]:
            tree = ast.parse(source_path.read_text())
            for call in ast.walk(tree):
                if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == "render_template"):
                    continue
                if not call.args or not isinstance(call.args[0], ast.Constant) or not isinstance(call.args[0].value, str):
                    continue
                template = call.args[0].value
                source = env.loader.get_source(env, template)[0]
                undeclared = meta.find_undeclared_variables(env.parse(source)) - globals_
                supplied = {kw.arg for kw in call.keywords if kw.arg}
                missing = sorted(undeclared - supplied)
                if missing:
                    failures.append((template, source_path.as_posix(), call.lineno, missing))
        self.assertEqual(failures, [])

    def test_literal_form_actions_and_fetch_targets_resolve(self):
        routes = _route_contract()
        failures = []
        for path in (ROOT / "templates").rglob("*.html"):
            source = path.read_text()
            for match in re.finditer(r'<form\b[^>]*\bmethod=["\']?(post|get)["\']?[^>]*>', source, re.I):
                tag = match.group(0)
                action_match = re.search(r'\baction=["\']([^"\']+)["\']', tag, re.I)
                if not action_match:
                    continue
                action = action_match.group(1)
                if "{{" in action or "{%" in action or action.startswith(("http", "#")):
                    continue
                method = re.search(r'\bmethod=["\']?(post|get)', tag, re.I).group(1).upper()
                route = action.split("?", 1)[0]
                if route and (route not in routes or method not in routes[route]):
                    failures.append((path.as_posix(), method, action, sorted(routes.get(route, set()))))
            for match in re.finditer(r'fetch\(\s*["\']([^"\']+)["\']', source):
                route = match.group(1).split("?", 1)[0]
                if route.startswith("/") and route not in routes:
                    failures.append((path.as_posix(), "FETCH", route, []))
        self.assertEqual(failures, [])

    def test_no_obvious_unsafe_execution_primitives(self):
        bad = []
        patterns = [r"\beval\s*\(", r"\bexec\s*\(", r"os\.system\s*\(", r"shell\s*=\s*True", r"pickle\.loads?\s*\("]
        for folder in ("routes", "services", "utils", "scripts", "database"):
            for path in (ROOT / folder).glob("*.py"):
                text = path.read_text()
                for pattern in patterns:
                    if re.search(pattern, text):
                        bad.append((path.as_posix(), pattern))
        self.assertEqual(bad, [])

    def test_request_status_updates_are_serialized_and_revalidated(self):
        text = (ROOT / "routes/main.py").read_text()
        self.assertIn('with_for_update()', text)
        self.assertIn('locked_allowed', text)
        self.assertIn('if new not in locked_allowed', text)
        self.assertIn('locked_is_customer', text)
        self.assertIn('locked_is_target', text)

    def test_all_templates_parse(self):
        env = Environment(loader=FileSystemLoader(str(ROOT / "templates")))
        count = 0
        for path in (ROOT / "templates").rglob("*.html"):
            env.parse(path.read_text())
            count += 1
        self.assertGreaterEqual(count, 60)

    def test_static_js_has_no_inline_php_endpoint_drift(self):
        app_js = (ROOT / "assets/js/app.js").read_text()
        # Legacy URLs may remain intentionally, but they must be represented by Flask routes.
        routes = _route_contract()
        for target in re.findall(r'["\'](/?[^"\']+\.php(?:\?[^"\']*)?)["\']', app_js):
            normalized = target.split("?", 1)[0]
            if not normalized.startswith("/"):
                normalized = "/" + normalized
            self.assertIn(normalized, routes)

    def test_python_source_compiles(self):
        for path in [ROOT / "app.py", *(ROOT / "config").glob("*.py"), *(ROOT / "database").glob("*.py"), *(ROOT / "models").glob("*.py"), *(ROOT / "routes").glob("*.py"), *(ROOT / "services").glob("*.py"), *(ROOT / "utils").glob("*.py"), *(ROOT / "scripts").glob("*.py")]:
            compile(path.read_text(), str(path), "exec")


if __name__ == "__main__":
    unittest.main()
