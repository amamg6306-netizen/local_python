# LocalConnect Production Hardening — Phase 2

Date: 2026-09-24  
Phase: B — security fixes and non-destructive migration foundation  
Release status: **NOT READY FOR LIVE PAYMENTS**

## Implemented

- Production configuration moved to process environment / secret-manager inputs. Production fails closed for missing `APP_KEY`, `APP_URL`, DB host/name/user/password, root DB user, or insecure session-cookie policy. Development retains XAMPP defaults only when `APP_ENV` is not `production`.
- Added `.env.example` with placeholders only; the application deliberately does not auto-load a public-web-root `.env` file.
- Added secure-cookie policy, strict cookie sessions, idle/absolute timeout, periodic session-ID rotation, proxy-aware HTTPS only for explicitly trusted proxy IPs, and `session_version` invalidation.
- Converted logout to POST + CSRF and changed the navbar logout UI to a form.
- Added database-backed login throttling by HMAC-pseudonymized email and client-IP buckets. User-facing login errors remain non-enumerating for invalid credentials.
- Added password-reset and email-verification token foundations. Tokens are random capability values; only SHA-256 validator hashes are stored. Delivery supports PHP `mail()` when explicitly configured; live mail delivery is still a deployment dependency.
- Added optional/production-required email verification policy.
- Added admin TOTP MFA with encrypted-at-rest MFA secret, anti-replay step tracking, session MFA gate, and a 10-minute admin re-authentication foundation for future payment configuration changes.
- Added upload dimension/pixel caps and image decode/re-encode when GD is available. Production defaults to reject uploads if secure re-encoding is unavailable. Upload destination is allowlisted and failed DB writes clean newly-created profile/portfolio files.
- Added application/security audit failure logging without printing passwords/tokens/secrets.
- Fixed the business subscription audience filter to `('business','both')`.
- Hardened `ensure_free_subscription()` with a transaction + user-row `FOR UPDATE` lock and recheck to remove its read/insert race. Full payment entitlement state constraints remain Phase 4 work.
- Added server-path denial `.htaccess` files for configuration, database, docs, tests, tools, and storage plus stronger Apache upload execution restrictions.
- Added `database/production/fresh_schema.sql`, a zero-demo-account fresh bootstrap for a pre-created production database, plus a sanitized non-destructive `database/localconnect_db.sql`. Known demo users/passwords and the destructive demo-reset SQL were removed from the production-hardening artifact. Local test accounts must be created explicitly.
- Added versioned, non-destructive production migration/preflight/rollback scripts and a CLI first-admin creation tool that takes credentials only from environment variables.

## Intentionally not claimed / deferred

- No payment gateway, payment-method UI, webhook or paid entitlement activation is enabled in Phase 2.
- The audit container has no PDO MySQL driver or MySQL/MariaDB service, so the production migration and DB-backed browser flows could not be executed here. The SQL is provided with preflight/rollback and must be rehearsed against a disposable clone before production.
- CSP/HSTS, reverse-proxy deployment policy, dependency/secret scanning, backup/restore rehearsal and production web-server rules outside Apache remain Phase 6 hardening work.
- Password-reset/email-verification delivery is not production-ready until the operator configures and verifies an approved transactional mail provider or equivalent delivery integration.
- Admin TOTP recovery-code lifecycle is not included in this phase; loss-of-authenticator operational recovery must be defined before a live admin rollout.

## Release gate

**NOT READY FOR LIVE PAYMENTS.** Phase 2 improves security prerequisites only. Paid purchase buttons remain disabled.
