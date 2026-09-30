# LocalConnect Production Hardening — Phase 1

Date: 2026-09-24  
Phase: A — inventory, threat model, and test baseline  
Release status: **NOT READY FOR LIVE PAYMENTS**

## Scope and integrity

The supplied `localconnect(1).zip` was extracted and reviewed as the Phase 1 source of truth. This phase intentionally does **not** enable live payments or change marketplace behavior. It adds audit/test artifacts so later phases can make controlled changes against a recorded baseline.

Input ZIP SHA-256: `74026f8755030010685506b92e7ab622ac14309697162d5f85a59acaf8610dc4`

Original project inventory before Phase 1 audit files were added:

- 58 PHP files
- 7 SQL files (`localconnect_db.sql` plus Phase 2–7 migrations)
- 81 total files
- PHP/MySQL/PDO application with customer, provider, business, and admin roles
- Bootstrap 5 and Font Awesome loaded from public CDNs
- Web-accessible `uploads/` containing Apache `.htaccess` execution restrictions

A machine-readable route/security inventory is in `docs/production/route_inventory.csv`.

## Verified starting points

The following items from the production-hardening brief are confirmed in the supplied source:

1. `config/database.php` hard-codes `127.0.0.1`, database `localconnect_db`, user `root`, and a blank password. There is no environment/secrets lookup.
2. `provider/subscription.php` and `business/subscription.php` show disabled purchase buttons; no real checkout is wired.
3. `business/subscription.php` incorrectly uses `audience IN ('provider','both')`. Business plans should use `('business','both')`.
4. `admin/payments.php` is a read-only ledger view. There is no admin payment-method CRUD or merchant configuration workflow.
5. No payment gateway SDK/API client, checkout-session endpoint, payment-method page, signed webhook handler, reconciliation worker, or idempotency implementation is present.
6. `payments`, `subscriptions`, and `subscription_plans` exist, but their current schema is insufficient for safe live payment lifecycle handling.
7. `ensure_free_subscription()` performs a read-then-insert without locking or a database uniqueness invariant preventing duplicate active/free subscriptions under concurrency.
8. `current_subscription()` selects the newest active, non-expired subscription but does not model a complete renewal/refund/dispute lifecycle.
9. Authentication uses `password_hash()` / `password_verify()`, session ID rotation after login/registration, role checks, and CSRF helpers.
10. Image uploads use Fileinfo MIME checks, a 3 MB size limit, and random filenames, but do not decode/re-encode images or bound dimensions/pixel count. Upload protection is Apache-specific.
11. `provider/available-requirements.php`, `provider/requests.php`, and `customer/requests.php` use unbounded `fetchAll()` result sets. This is recorded as a performance/memory risk, **not** a confirmed memory leak.
12. The fresh SQL seed contains demo users/credentials and starts by dropping application tables. It must not be used as a production migration.

## Existing controls worth preserving

Static review found useful controls that should be retained during hardening:

- PDO is configured with exceptions and `PDO::ATTR_EMULATE_PREPARES => false`.
- Most database interactions use prepared statements. Dynamic SQL fragments reviewed in search/request/admin code are selected from server-side whitelists or fixed field choices rather than directly trusting arbitrary SQL text from the browser.
- The audit scanner detected 22 POST handlers; all 22 contain CSRF validation (`verify_csrf()` or equivalent `hash_equals()` handling in the AJAX favorite endpoint).
- Role/ownership checks exist on provider, business, customer, admin, service-request, review, favorite, notification, and report flows.
- Output is generally escaped with `e()`; no direct echo of `$_GET` / `$_POST` was found in the static pass.
- Request claiming uses a transaction and `SELECT ... FOR UPDATE` to prevent two providers from claiming the same open requirement simultaneously.
- Review creation verifies ownership and completed-request status and the database has a unique constraint on `reviews.request_id`.
- Favorites have a uniqueness constraint on `(customer_id, target_user_id)`.
- Common security headers currently include `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and a `Permissions-Policy`.

These findings are evidence from static review, not a claim that the application is free of SQL injection, XSS, IDOR, or other vulnerabilities. Later phases add regression tests and runtime verification.

## Architecture and trust boundaries

### Trust boundaries

1. **Browser ↔ PHP application** — untrusted form fields, query parameters, cookies, uploads, and future payment-return parameters enter here.
2. **PHP application ↔ MySQL** — identity, role, marketplace, subscription, payment, and audit state are persisted here.
3. **Web server ↔ uploads directory** — user-controlled bytes are stored under a web-accessible path.
4. **Application ↔ CDN assets** — Bootstrap/Font Awesome are currently third-party runtime dependencies.
5. **Admin browser ↔ privileged application routes** — verification, blocking, moderation, advertising, and future payment configuration have high impact.
6. **Future application ↔ payment service provider** — merchant credentials, checkout session creation, webhooks, refunds, reconciliation, and recurring events will cross this boundary.
7. **Future application ↔ email/SMS/secret manager/logging/backup systems** — not implemented in the current repository, but required for production operations.

### High-value assets

- User password hashes and sessions
- Customer/provider/business personal and contact data
- Service requests, addresses, reviews, reports, and notification records
- Admin privileges and moderation actions
- Subscription entitlements and payment state
- Future PSP credentials/webhook secrets
- Manual bank/UPI merchant instructions and reconciliation records
- Audit records, backups, and deployment secrets

## Threat model

| Threat area | Current observation | Risk / later control |
|---|---|---|
| Account takeover | No login throttling, password reset, or email verification | Add throttling, reset/verification lifecycle, logging, lockout safeguards |
| Admin takeover | Admin is password-only; no MFA or sensitive-action re-authentication | Add TOTP/WebAuthn-capable MFA foundation and re-auth gates |
| Session abuse | Session rotation exists; no explicit idle/absolute timeout; secure cookie depends on direct HTTPS detection | Add strict session settings, proxy-aware HTTPS handling, timeouts, logout POST/CSRF |
| IDOR / authorization | Core routes contain role/ownership checks | Build route-level regression tests; verify all IDs server-side in Phase 2 |
| CSRF | Detected POST handlers have CSRF checks | Preserve and test; move logout to POST |
| XSS | Central `e()` helper widely used | Add context-specific URL/attribute validation and CSP; regression payload tests |
| SQL injection | Prepared statements are prevalent | Continue audit of dynamic fragments and add negative tests |
| Upload abuse | MIME/size/random name controls exist | Decode/re-encode or robustly inspect images, cap dimensions/pixels, validate paths, server-independent execution denial, orphan cleanup |
| Secrets leakage | DB credentials in source; no secret manager/env pattern | Environment/secrets configuration, redacted logs, secret scanning |
| Payment spoofing | No checkout/webhook implementation yet | Only signed PSP webhooks + reconciliation may grant entitlements |
| Payment replay/duplication | No external ID uniqueness/idempotency model | Add idempotency keys, unique external IDs, event table, transactional state machine |
| Manual-payment fraud | Not implemented | Keep pending until admin verification; audit all reconciliation decisions |
| Denial of service | Several unbounded result sets and no login rate limiting | Pagination, bounded uploads, throttling, measured load tests |
| Repudiation | `platform_activity` covers some admin actions only | Expand immutable/auditable security/payment event coverage |
| Migration/data loss | Fresh SQL drops tables; some historical migrations are run-once only | Versioned non-destructive migrations, backup/rollback checks |

## Prioritized findings

### High / production blockers

**P1-SEC-001 — Production secrets/configuration are not externalized.** `root` + blank DB password is hard-coded. Production must fail closed when required secrets are missing rather than falling back to XAMPP defaults.

**P1-SEC-002 — Demo credentials/data are inside the deployable SQL seed.** README and SQL disclose known development passwords. Production seed/migrations must contain zero demo credentials.

**P1-SEC-003 — Authentication lifecycle is incomplete.** There is no login throttling, password-reset flow, email verification, or admin MFA. These are required before an Internet-facing launch.

**P1-PAY-001 — Live payment processing does not exist and must remain disabled.** There is no PSP checkout, webhook signature verification, event idempotency, reconciliation, refund/dispute handling, or payment-method administration. No current record may be treated as proof of payment.

**P1-PAY-002 — Subscription state has concurrency/state-model gaps.** Multiple active subscriptions are possible and `ensure_free_subscription()` can race. Payment enablement must first add transactional state transitions and database constraints.

**P1-UPLOAD-001 — Upload controls are incomplete for hostile production input.** Current MIME/size/random-name checks are a useful baseline, but image decoding/resource caps and server-independent execution blocking are missing.

### Medium

**P1-FUNC-001 — Business plan audience filter is wrong.** Business subscription page queries provider plans.

**P1-SESSION-001 — Session hardening is incomplete.** No idle/absolute expiry and logout is GET-triggered. HTTPS detection is not reverse-proxy aware.

**P1-HTTP-001 — HSTS and CSP are missing.** Existing response headers are helpful but not a production policy.

**P1-PERF-001 — Unbounded database reads exist.** The three specifically identified request pages are confirmed; the inventory also flags additional list pages for pagination review. No leak is claimed without profiling.

**P1-DB-001 — Fresh install SQL is destructive.** `localconnect_db.sql` drops tables and is unsuitable for production upgrades. Some historical index migrations are not idempotent if re-run.

**P1-AUDIT-001 — Audit coverage is partial.** `log_activity()` silently suppresses all exceptions, and authentication/security/payment events are not comprehensively recorded.

**P1-VALID-001 — Server-side validation is inconsistent.** Several fields rely mainly on HTML limits/types; production code should enforce lengths, numeric ranges, dates, URLs, and allowed values on the server.

### Informational / architecture debt

- `base_url()` is fixed to `/localconnect/`; production subpath/domain configuration is not externalized.
- Bootstrap and Font Awesome are runtime CDN dependencies with no application CSP yet.
- Contact email delivery, observability, backups, queueing, and dependency/secret scanning are not implemented.

## Payment data-model gap summary

Current `payments` contains user, subscription, provider name, provider payment ID, amount, currency, and a small status enum. Before payment enablement it needs, at minimum, immutable plan/price/tax snapshots, internal order/payment identifiers, unique provider order/payment/event IDs, idempotency keys, attempt/status history, failure/cancellation/refund/dispute metadata, timestamps, reconciliation state, and indexes/constraints supporting exactly-once entitlement effects.

Current `subscriptions` permits multiple simultaneous `active` rows and lacks a full status transition/history model. The future implementation must make entitlement changes transactional with the verified payment/reconciliation event.

## Phase 2 entry criteria

Phase 2 may start from this exact tree. It should address production configuration/secrets, demo-data separation, auth/session hardening, server-side validation/authorization coverage, upload hardening, admin MFA/re-auth foundation, audit logging, and safe non-destructive migrations **before** live checkout is introduced.

No live payment charge or production deployment is approved by Phase 1.
