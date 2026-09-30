# Database migrations

LocalConnect already has an audited production migration chain under `database/production/` with matching preflight and rollback files. That directory remains authoritative so existing release tooling and checks are not broken.

The Python migration runner in `scripts/migrate_db.py` discovers only forward migrations matching `YYYYMMDD_NNN_name.sql` from `database/production/`. It excludes `_preflight.sql`, `_rollback.sql`, `fresh_schema.sql`, and grant templates.

`database/schema.sql` mirrors the current fresh-install schema snapshot. Use `scripts/init_db.py` only for an empty, pre-created database. Existing databases must use the migration runner instead of being recreated.
