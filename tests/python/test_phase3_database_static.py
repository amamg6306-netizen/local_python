from __future__ import annotations

import ast
import hashlib
import json
import re
import unittest
from pathlib import Path



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

    def test_postgresql_schema_is_canonical_and_contains_all_tables(self):
        schema = (ROOT / "database" / "postgresql_schema.sql").read_text(encoding="utf-8")
        canonical = (ROOT / "database" / "schema.sql").read_text(encoding="utf-8")
        fresh = (ROOT / "database" / "production" / "fresh_schema.sql").read_text(encoding="utf-8")
        self.assertEqual(hashlib.sha256(schema.encode()).hexdigest(), hashlib.sha256(canonical.encode()).hexdigest())
        self.assertEqual(hashlib.sha256(canonical.encode()).hexdigest(), hashlib.sha256(fresh.encode()).hexdigest())
        for table in self.manifest:
            self.assertIn(f"CREATE TABLE {table}", schema)

    def test_postgresql_schema_does_not_use_mysql_storage_syntax(self):
        schema = (ROOT / "database" / "postgresql_schema.sql").read_text(encoding="utf-8").lower()
        for forbidden in ("engine=innodb", "auto_increment", "unsigned", "information_schema", "insert ignore", "on duplicate key"):
            self.assertNotIn(forbidden, schema)

    def test_postgresql_bootstrap_files_are_present(self):
        self.assertTrue((ROOT / "database" / "postgresql_schema.sql").exists())
        self.assertTrue((ROOT / "scripts" / "init_db.py").exists())
        self.assertTrue((ROOT / "scripts" / "check_db_schema.py").exists())
        self.assertIn("postgresql+psycopg", (ROOT / "config" / "settings.py").read_text(encoding="utf-8"))

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
