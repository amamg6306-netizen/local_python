from __future__ import annotations

import unittest

IMPORT_ERROR = None
try:
    from app import create_app
    from config.settings import TestingConfig
    from extensions import db
    import models  # noqa: F401
except ModuleNotFoundError as exc:
    IMPORT_ERROR = exc



class Phase3DatabaseRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if IMPORT_ERROR is not None:
            raise unittest.SkipTest(f"Phase 3 runtime dependencies are not installed: {IMPORT_ERROR}")
        cls.app = create_app(TestingConfig)

    def test_all_effective_tables_are_registered(self):
        with self.app.app_context():
            self.assertEqual(len(db.metadata.tables), 32)
            self.assertIn("payments", db.metadata.tables)
            self.assertIn("service_requests", db.metadata.tables)
            self.assertIn("admin_mfa", db.metadata.tables)

    def test_sqlite_test_schema_can_be_created(self):
        with self.app.app_context():
            db.create_all()
            inspector = db.inspect(db.engine)
            self.assertEqual(len(inspector.get_table_names()), 32)
            db.drop_all()


if __name__ == "__main__":
    unittest.main()
