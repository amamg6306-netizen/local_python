# LocalConnect — Native Python Render deployment

This repository deploys as a Render **Native Python Web Service**. Docker, Apache, PHP runtime, Nginx configuration and `.htaccess` are not production dependencies.

## Render Blueprint

`render.yaml` configures:

- runtime: `python`
- Python: `3.13.15`
- plan: `0.5c-512mb` (paid; required for the attached persistent disk)
- build: `pip install -r requirements.txt`
- pre-deploy: `python scripts/check_config.py && python scripts/init_db.py --yes && python scripts/check_db_schema.py`
- start: `gunicorn app:app --bind 0.0.0.0:$PORT`
- health check: `/health`
- disk: `/var/data/localconnect/uploads`, 1 GB
- cron: `localconnect-payment-reconciliation`, every 5 minutes, running `python scripts/payment_reconciliation_worker.py --limit=20`

The cron service reuses the web service database/payment secrets through Blueprint `fromService` references. It intentionally uses temporary upload storage because reconciliation does not read or write user uploads.

The health endpoint executes a bounded `SELECT 1` probe. It returns 503 without exposing diagnostics if the primary DB is unavailable.

## Required account-level configuration

Before the first production deploy, set the Blueprint's `sync: false` values in Render:

- `SECRET_KEY`
- `APP_KEY` only if legacy encrypted admin-MFA records still exist
- `APP_URL`
- `DATABASE_URL`
- `APP_MAIL_FROM`
- `SMTP_HOST`
- `SMTP_USERNAME` if required by the mail server
- `SMTP_PASSWORD` if required by the mail server
- `PAYMENT_RAZORPAY_KEY_ID` if Razorpay is enabled
- `PAYMENT_RAZORPAY_KEY_SECRET` if Razorpay is enabled
- `PAYMENT_RAZORPAY_WEBHOOK_SECRET` if Razorpay is enabled
- `PAYMENT_RAZORPAY_WEBHOOK_IP_ALLOWLIST` only if an approved fixed allowlist is available

`PAYMENT_ALLOW_LIVE=false` remains the deployment default. Use sandbox credentials until the complete payment release gate has passed.

## Database preparation

The application now targets PostgreSQL using `psycopg` 3. Render's PostgreSQL `DATABASE_URL` is accepted directly and normalized to
`postgresql+psycopg://...`. The normal PostgreSQL port is `5432`.

For a fresh database, the Render pre-deploy command automatically runs:

```bash
python scripts/init_db.py --yes
python scripts/check_db_schema.py
```

`init_db.py` is non-destructive: it creates missing tables/indexes and seeds the application's categories, services and subscription plans without dropping existing data.

For an existing PostgreSQL database:

1. Take and verify a database backup.
2. Run `python scripts/check_db_schema.py`.
3. Run `python scripts/init_db.py --yes` to create any missing model objects.
4. Run `python scripts/check_db_schema.py` again.
5. Review application logs and perform the live smoke tests below.

The old MySQL/MariaDB SQL files are retained only as historical migration evidence; they are not used by the PostgreSQL deployment path.

The Render pre-deploy command intentionally blocks a release if configuration is invalid or the effective schema is incomplete.

## Persistent uploads

Render's ordinary filesystem is ephemeral. The Blueprint mounts a persistent disk at `/var/data/localconnect/uploads` and configures the application to store profile, business-logo and portfolio images there.

If migrating existing uploads, run from the deployed service environment after the disk is attached:

```bash
python scripts/sync_uploads_to_storage.py --source <legacy-upload-root>
```

The synchronizer does not overwrite differing existing files and reports conflicts.

A Render persistent disk is attached to only one service instance. Do not scale this service to multiple instances while local persistent-disk uploads are in use; move uploads to shared object storage first.

## First deploy verification

After the deploy becomes live, verify at minimum:

1. `/health` returns HTTP 200.
2. Public home/search/profile pages render and static assets load.
3. Register/login/logout/email verification/password reset.
4. Customer/provider/business/admin role boundaries.
5. Customer request creation and request status lifecycle.
6. Provider/business service/profile workflows and uploads.
7. Favorites, notifications, reviews and reports.
8. Admin CRUD/moderation/MFA/re-auth operations.
9. Razorpay **sandbox** checkout, callback, signed webhook and reconciliation if Razorpay is enabled.
10. Manual payment review flow if enabled.
11. The payment-reconciliation cron appears in Render, runs successfully, and does not accumulate retryable jobs unexpectedly.
12. Render logs contain no stack traces/secrets and show no unexpected 4xx/5xx failures.

Do not mark deployment complete until the live URL and critical routes have been checked.
