# Phase 4 — Authentication, Sessions and Security Migration

Phase 4 implements the Flask/Python equivalent of the legacy authentication and administrator-authentication surface while keeping the original PHP source available as migration evidence.

## Implemented routes

- `/login.php` compatibility redirect
- `/logout.php` POST compatibility logout
- `/register.php` compatibility redirect
- `/auth/login.php`
- `/auth/logout.php`
- `/auth/register.php`
- `/auth/forgot-password.php`
- `/auth/reset-password.php`
- `/auth/resend-verification.php`
- `/auth/verify-email.php`
- `/admin/mfa.php`
- `/admin/reauth.php`

## Security parity

- Existing PHP bcrypt hashes (`$2y$`) remain accepted; new hashes use bcrypt cost 12 and remain PHP-compatible.
- Login rate limits preserve email and client-IP HMAC buckets.
- Blocked and pending-account behavior is preserved.
- Password reset tokens use selector + SHA-256 validator hashes, expiry, row locking during consumption, and `session_version` invalidation.
- Email-verification resend uses an opaque response and rate limiting to reduce account enumeration.
- Flask-WTF protects browser POST forms; CSRF failures return the legacy-style 419 message.
- Session cookies remain HttpOnly/SameSite=Lax and secure in production. Login clears prior client session state; idle, absolute and rotation timestamps are enforced and a signed random rotation nonce is refreshed periodically. `session_version` provides server-side revocation after password reset/block actions.
- Role guards are server-side. Admin routes enforce TOTP MFA when configured/required.
- TOTP replay protection preserves `last_used_step` behavior.
- Existing admin-MFA records are readable in both legacy `sodium_secretbox` and `aes-256-gcm` formats. Preserve the original production `APP_KEY` during migration until all existing MFA records are intentionally re-encrypted/re-enrolled.
- Sensitive-admin helper gates for verified MFA and recent password reauthentication are available for payment/admin routes migrated in later phases.

## Mail delivery

The legacy PHP `mail()` dependency is replaced by configurable SMTP for Native Python deployment. Development can use `APP_MAIL_DRIVER=log`. Production SMTP configuration uses `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS`, and `APP_MAIL_FROM`.

## UI parity

Auth/admin-auth Jinja templates retain the original Bootstrap layout, CSS classes, labels, links, form fields and the existing `assets/css/style.css` / `assets/js/app.js`. Phase 3 → Phase 4 hash comparison reports zero modifications to the legacy PHP/CSS/JS/image asset set.

## Verification

- Python compile: PASS.
- Phase 4 auth static suite: 10/10 PASS.
- Existing Phase 1–6 PHP security/payment/performance suites: PASS.
- PHP syntax: 93/93 PASS.
- Secret scan: PASS.
- Legacy PHP/CSS/JS/image baseline integrity: PASS (0 changed, 0 missing).
- Runtime Flask auth suite is included at `tests/python/test_phase4_auth_runtime.py`. It is intentionally not claimed as executed in this audit environment because package installation cannot reach PyPI; it skips cleanly when Flask dependencies are unavailable.
