# Render Environment Variables — LocalConnect PostgreSQL

Do not upload a real `.env` file to Git/Render. Set these values in the Render Web Service Environment tab.

## Required

- `APP_ENV=production`
- `APP_DEBUG=false`
- `APP_URL=https://YOUR-SERVICE.onrender.com`
- `SECRET_KEY=<long random secret, at least 32 bytes>`
- `DATABASE_URL=<Render PostgreSQL Internal Database URL>`
- `APP_MAIL_FROM=<verified sender email>`
- `SMTP_HOST=<SMTP host>`
- `TRUSTED_HOSTS=YOUR-SERVICE.onrender.com`
- `SESSION_COOKIE_SECURE=true`
- `FORCE_HTTPS=true`
- `APP_ADMIN_MFA_REQUIRED=true`
- `APP_REQUIRE_EMAIL_VERIFICATION=true`
- `UPLOAD_REQUIRE_REENCODE=true`
- `UPLOAD_STORAGE_BACKEND=filesystem`
- `UPLOAD_STORAGE_ROOT=/var/data/localconnect/uploads`
- `UPLOAD_DISK_REQUIRED=true`
- `SECURITY_CSP_MODE=enforce`

## PostgreSQL

Keep the Render PostgreSQL port as `5432`. Do not replace it with `3306`.

The `DATABASE_URL` should be the PostgreSQL URL supplied by Render, for example:

`postgresql://USER:PASSWORD@HOST:5432/DATABASE`

The application converts this internally to the SQLAlchemy `postgresql+psycopg` form.

## Optional

- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_PORT=587`
- `SMTP_USE_TLS=true`
- Razorpay variables if payments are enabled.
- `APP_KEY` only if required for legacy encrypted MFA records.

Never put actual passwords, API secrets, webhook secrets, or production `SECRET_KEY` values in this repository or ZIP.


## Important production rule

`DATABASE_URL` must be the actual Render PostgreSQL **Internal Database URL**. Do not set `DATABASE_URL` or `DB_HOST` to `127.0.0.1`, `localhost`, or `::1`. The application now fails fast with a clear configuration error instead of attempting a localhost connection.

## Runtime diagnostic

At startup the application logs the resolved PostgreSQL driver, host, port, and database name, without logging the username or password. On Render, a missing `DATABASE_URL` no longer falls back to `127.0.0.1`; the service fails with a configuration error instead.
