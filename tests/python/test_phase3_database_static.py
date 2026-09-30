from __future__ import annotations

import ast
import hashlib
import json
import re
import unittest
from pathlib import Path

from database.sql_runner import iter_mysql_statements, strip_database_switches


ROOT = Path(__file__).resolve().parents[2]
MODEL_FILES = [
    ROOT / "models" / "core.py",
    ROOT / "models" / "marketplace.py",
    ROOT / "models" / "security.py",
    ROOT / "models" / "billing.py",
]


def model_shape() -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for path in MODEL_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            table_name = None
            columns: set[str] = set()
            uses_timestamp_mixin = any(
                isinstance(base, ast.Name) and base.id == "TimestampMixin" for base in node.bases
            )
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name) and target.id == "__tablename__":
                            if isinstance(item.value, ast.Constant) and isinstance(item.value.value, str):
                                table_name = item.value.value
                        elif isinstance(target, ast.Name) and isinstance(item.value, ast.Call):
                            func = item.value.func
                            if (
                                isinstance(func, ast.Attribute)
                                and func.attr == "Column"
                                and isinstance(func.value, ast.Name)
                                and func.value.id == "db"
                            ):
                                columns.add(target.id)
            if table_name:
                if uses_timestamp_mixin:
                    columns.update({"created_at", "updated_at"})
                result[table_name] = columns
    return result


class Phase3DatabaseStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "database" / "schema_manifest.json").read_text(encoding="utf-8"))["tables"]
        cls.shape = model_shape()
        cls.model_source = "\n".join(path.read_text(encoding="utf-8") for path in MODEL_FILES)

    def test_effective_schema_has_32_tables(self):
        self.assertEqual(len(self.manifest), 32)
        self.assertEqual(set(self.shape), set(self.manifest))

    def test_model_columns_match_effective_schema(self):
        differences = {}
        for table, spec in self.manifest.items():
            expected = set(spec["columns"])
            actual = self.shape[table]
            if expected != actual:
                differences[table] = {
                    "missing": sorted(expected - actual),
                    "extra": sorted(actual - expected),
                }
        self.assertEqual(differences, {})

    def test_named_constraints_and_indexes_are_mapped(self):
        expected_names: set[str] = set()
        for spec in self.manifest.values():
            for key in ("indexes", "unique_constraints", "foreign_keys", "checks"):
                expected_names.update(spec[key])
        missing = sorted(name for name in expected_names if name not in self.model_source)
        self.assertEqual(missing, [])

    def test_canonical_schema_copy_matches_fresh_snapshot(self):
        schema = (ROOT / "database" / "schema.sql").read_bytes()
        fresh = (ROOT / "database" / "production" / "fresh_schema.sql").read_bytes()
        self.assertEqual(hashlib.sha256(schema).hexdigest(), hashlib.sha256(fresh).hexdigest())

    def test_mysql_sql_parser_accepts_all_database_sql(self):
        files = [ROOT / "database" / "schema.sql", *sorted((ROOT / "database" / "production").glob("*.sql"))]
        for path in files:
            with self.subTest(path=path.name):
                statements = list(iter_mysql_statements(path.read_text(encoding="utf-8")))
                self.assertGreater(len(statements), 0)

    def test_database_switches_are_removed_by_runner(self):
        sql = "-- migration header\nUSE localconnect_db; SELECT 'a;b' AS value; SELECT 2;"
        statements = list(strip_database_switches(iter_mysql_statements(sql)))
        self.assertEqual(statements, ["SELECT 'a;b' AS value", "SELECT 2"])

        production_sql = (ROOT / "database" / "production" / "20260924_001_security_foundation.sql").read_text(encoding="utf-8")
        stripped = list(strip_database_switches(iter_mysql_statements(production_sql)))
        self.assertFalse(any(re.search(r"\bUSE\s+localconnect_db\b", statement, re.I) for statement in stripped))

    def test_forward_migration_set_excludes_preflight_and_rollback(self):
        forward = []
        pattern = re.compile(r"^\d{8}_\d{3}_[a-z0-9_]+\.sql$")
        for path in sorted((ROOT / "database" / "production").glob("*.sql")):
            if path.stem.endswith(("_preflight", "_rollback")):
                continue
            if pattern.match(path.name):
                forward.append(path.name)
        self.assertEqual(
            forward,
            [
                "20260924_001_security_foundation.sql",
                "20260924_002_payment_methods.sql",
                "20260924_003_checkout_webhooks.sql",
                "20260924_004_performance_reliability.sql",
                "20260924_005_production_hardening.sql",
            ],
        )

    def test_critical_effective_statuses_are_present(self):
        expected_literals = {
            "subscription_status": {"active", "scheduled", "expired", "cancelled", "pending", "suspended"},
            "payment_status": {"pending", "paid", "failed", "cancelled", "refunded", "partially_refunded", "disputed", "requires_review"},
            "request_status": {"pending", "accepted", "rejected", "in_progress", "completed", "cancelled"},
        }
        for enum_name, values in expected_literals.items():
            self.assertIn(f'enum_type("{enum_name}"', self.model_source)
            for value in values:
                self.assertIn(f'"{value}"', self.model_source)


if __name__ == "__main__":
    unittest.main()
