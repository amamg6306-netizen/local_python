# LocalConnect PostgreSQL migration

The current deployment target is PostgreSQL.

## Connection

Preferred Render variable:

```text
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DATABASE
```

The application normalizes this to SQLAlchemy's `postgresql+psycopg://` driver URL.
Do not use `127.0.0.1` for a production database unless PostgreSQL is actually running inside the same container.

## Schema

- `database/postgresql_schema.sql` is the canonical PostgreSQL fresh schema.
- `database/schema.sql` and `database/production/fresh_schema.sql` are synchronized copies.
- `scripts/init_db.py --yes` creates missing tables/indexes and seeds categories, services and subscription plans.
- `scripts/check_db_schema.py` verifies the live database against `database/schema_manifest.json`.

## Render pre-deploy

```bash
python scripts/check_config.py && python scripts/init_db.py --yes && python scripts/check_db_schema.py
```

This path is non-destructive: it does not drop application tables or data.

## Important

The old MySQL/MariaDB SQL migration files are retained for historical/audit reference only. They must **not** be executed against PostgreSQL. Future schema changes should be made in the SQLAlchemy models and the PostgreSQL bootstrap/migration path.
