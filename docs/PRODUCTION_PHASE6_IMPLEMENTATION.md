# LocalConnect Production Phase 6 — implementation summary

Phase 6 is cumulative on Production Phase 5 and preserves the marketplace roles and core workflows.

## Runtime and browser hardening

- `config/app.php` now applies production error-display policy and a fail-closed HTTPS redirect that trusts forwarded protocol only from explicitly allowlisted proxies.
- Production config validation requires HTTPS, debug-off, Secure session cookies, admin MFA, email verification, GD upload re-encode, enforcing CSP and a one-year HSTS minimum.
- `includes/security.php` centralizes nonce CSP, HSTS, frame denial, MIME sniffing protection, restrictive permissions/referrer policies and API no-store headers.
- Existing inline JavaScript event attributes were removed; CSP can enforce `script-src-attr 'none'`. Necessary inline bootstrap/payment scripts use a per-request nonce.
- AJAX favorites now use the configured base path instead of a hard-coded `/localconnect/` endpoint and avoid `innerHTML` assignment.
- `.htaccess` blocks source/config/deployment artefacts and executable uploads; example Apache/PHP production configs are included under `deploy/`.

## Authentication and recovery

- Strict cookie-only sessions now explicitly disable URL-transmitted session IDs.
- Successful logins opportunistically rehash passwords when PHP's current default algorithm/cost changes.
- Password-reset and verification-resend delivery have separate email/IP hashed rate-limit buckets and keep enumeration-safe responses.

## Webhook/log hardening

- Razorpay webhook `Content-Length` is rejected before reading a body larger than 1 MiB; the existing raw-body HMAC and idempotent/reconciliation flow remains authoritative.
- Security logging removes secret-bearing keys and redacts common credential/token patterns before writing server logs.

## Database and operations

- `20260924_005_production_hardening.sql` adds idempotent support indexes for auth-token cleanup, actor audit lookup, checkout expiry and reconciliation-job lookup. Preflight/rollback companions are included.
- `least_privilege_grants.template.sql` separates ordinary web DML rights from DBA/migration privileges.
- Backup/restore shell tools use temporary `0600` MySQL client configuration rather than command-line passwords.
- Secret scan, external-dependency inventory and a fail-closed release gate were added.
- Release evidence is intentionally stored outside source-controlled examples under `storage/release_evidence/` on the deployed environment.

## Release posture

The code package is not sufficient evidence for live charging. The final gate requires real migration/restore, mail, sandbox payment, performance, independent security, legal/financial and production-smoke evidence. Until then, `PAYMENT_ALLOW_LIVE=false` stays the safe default.
