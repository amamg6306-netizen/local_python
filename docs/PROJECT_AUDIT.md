# LocalConnect Complete Project Audit

## Phase 1 conclusion

The supplied repository is a server-rendered PHP/MySQL local-services marketplace with four account roles (`customer`, `provider`, `business`, `admin`), a public discovery/search layer, request marketplace, reviews/favorites/notifications/reporting, provider/business management, administrator moderation, and a hardened subscription/payment subsystem. The current tree is materially more advanced than its historical early-phase documentation: the **current source code** is the migration source of truth.

No application code was rewritten in Phase 1. This phase records behavior and migration traceability before the Flask conversion begins.

## Audit coverage

- Files visited recursively: **215**
- Directories: **41** including repository root
- Approximate text lines visited: **8,580**
- File-type counts: .php: 93, .md: 39, .sql: 24, .txt: 14, [no extension]: 12, .py: 11, .sh: 10, .example: 3, .pyc: 3, .json: 2, .css: 1, .svg: 1, .js: 1, .csv: 1
- PHP files linted: **93 / 93 syntax PASS**
- SQL files audited: **24**
- Web route/page mappings: **69** plus one admin template partial
- Effective database tables: **32**
- Every supplied file is recorded with byte size and SHA-256 in `docs/PHASE1_FILE_AUDIT.csv`.

## Existing architecture

### Request/runtime flow

Browser → Apache/PHP route → `includes/auth.php`/`config/database.php` → PDO/MySQL → server-rendered PHP HTML. Shared header/footer inject Bootstrap 5.3.3, Font Awesome 6.5.2, the project stylesheet, Bootstrap JS, project JavaScript, CSRF token and base URL. Razorpay hosted checkout is loaded only on the gateway page.

### Main production areas

- **Public:** home, category browsing, search, provider/business profiles, about/privacy/terms/contact.
- **Authentication:** role-aware registration, login, POST logout, email verification, resend, forgot/reset password, throttling, password rehashing, session invalidation/versioning.
- **Customer:** dashboard, direct service requests, open requirements, request tracking, cancel transitions, favorites, reviews, reports and notifications.
- **Provider:** dashboard, profile, service offerings, portfolio uploads, incoming requests, open requirement matching/claiming, subscription/billing.
- **Business:** dashboard, business profile/logo/category/hours, service offerings, shared request workflow, subscription/billing.
- **Admin:** KPI/activity dashboard, user blocking, provider/business verification, categories, services, requests, reviews, reports, advertisements, subscriptions, payments, payment-method configuration, MFA and recent password re-authentication.
- **Billing:** server-priced plans, checkout intents, immutable payment snapshots, Razorpay order/callback/webhook flow, manual UPI/bank references, admin reconciliation, refunds/disputes, payment status history, entitlement activation/suspension and bounded retry worker.
- **Operations:** versioned migrations/preflights/rollbacks, backup/restore scripts, release gate, config checker, secret/dependency inventory, performance probes and reconciliation worker.

## Authentication and authorization model

The database role enum is exactly `customer|provider|business|admin`. Route protection is server-side through `require_login()` and `require_role()`. Blocked users and `session_version` changes invalidate sessions. Admin routes require MFA when configured/required; sensitive payment configuration and payment operations additionally use recent password re-authentication. Session controls include strict cookie mode, HttpOnly, SameSite=Lax, optional Secure, idle/absolute expiry and periodic session-ID rotation.

## Request marketplace workflow

Two request types exist:

1. **Direct request** — customer chooses a specific provider/business and one of that account's active offered services.
2. **Requirement** — customer posts an open request for a service; an eligible provider/business offering that service can claim it atomically.

After assignment, allowed state transitions are enforced server-side. Customer can cancel while `pending` or `accepted`. Assigned provider/business can move `pending → accepted|rejected`, `accepted → in_progress|cancelled`, and `in_progress → completed|cancelled`. Every change writes `request_status_history`; relevant parties receive notifications. Completed customer requests become eligible for one review per request.

## Frontend/UI inventory

The UI is server-rendered Bootstrap with one project CSS file and one project JS file. Important JS behavior to preserve: role-card selection; category→service filtering; confirmation before destructive forms; auto-submit filters; AJAX favorite toggling; CSRF/base-URL globals. Existing HTML structure, Bootstrap classes, Font Awesome icons, responsive cards/tables/forms, status badges, flash alerts and pagination should be retained rather than redesigned.

## Database architecture

`database/production/fresh_schema.sql` produces 32 effective tables. The project has both historical phase migrations and production migrations with preflight/rollback support. Major domains are identity/auth, profiles/catalogue, service requests/reviews/favorites/notifications/moderation, subscriptions/featured/lead allowances, payment methods/audit, checkout/payment/webhook/reconciliation, and platform activity. Full columns, keys, relationships and state enums are in `docs/DATABASE_MAP.md`.

## Security controls found in the current tree

- Password hashing/verification with rehash-on-login.
- CSRF checks on browser state-changing forms.
- Native prepared statements / parameterized SQL.
- Output escaping helper for templates.
- Login and auth-action rate limiting.
- Email verification and hashed reset/verify token storage.
- Admin TOTP MFA with encrypted secret material and replay-step protection.
- Recent admin password re-authentication for sensitive payment operations.
- CSP nonce, HSTS policy, X-Frame-Options, nosniff, referrer/permissions policies.
- Upload MIME/size/dimension/pixel validation, random filenames, managed-folder allowlist and production re-encoding policy.
- Log redaction for sensitive values.
- Webhook raw-body HMAC validation, body-size cap, replay/idempotency storage and optional source-IP allowlist.
- Live Razorpay keys blocked unless `PAYMENT_ALLOW_LIVE=true`.
- Pagination limits and bounded reconciliation queue/retry settings.

## File uploads and persistence

Uploads are currently placed under `uploads/profiles`, `uploads/businesses` and `uploads/portfolio`; paths are stored in MySQL. The existing Apache `.htaccess` prevents executable handling, but Render Native Python cannot rely on that and Render's ordinary filesystem is ephemeral. Phase 7 must choose persistent object storage or an appropriate persistent disk and keep the same public-path behavior.

## External dependencies / integrations

- MySQL/MariaDB.
- Bootstrap 5.3.3 CDN.
- Font Awesome 6.5.2 CDN.
- Razorpay API + hosted checkout + webhook.
- PHP `mail()`-style outbound email abstraction in the current implementation.
- Apache/PHP server configuration exists today but must not survive as a production dependency after migration.

## Current configuration surface

Environment variables discovered in current code include application URL/base path/key/debug/environment, DB host/port/name/user/password, secure-session settings/timeouts, trusted proxy settings, email verification/mail driver, admin MFA requirement, upload bounds/re-encoding, Razorpay keys/webhook/live-mode guard, pagination/performance telemetry limits and reconciliation-worker bounds. The Python migration should retain equivalent semantics while renaming only where necessary; `DB_PASSWORD` should become the preferred Render-facing password variable.

## Current known behavior that is easy to accidentally change

- `contact.php` currently **validates only** and explicitly states delivery is not configured; it does not create a DB record. This is existing behavior, not a missing route discovered by the audit.
- Root `login.php` and `register.php` are compatibility redirects; root `logout.php` is a real POST+CSRF compatibility handler.
- `business/requests.php` intentionally reuses the provider/business shared request implementation.
- Existing `.php` URL shapes are used throughout HTML/JS; Flask should preserve them during migration even though PHP is removed.
- Billing entitlements are not activated from a browser callback or a submitted manual reference alone.
- Automatic recurring charging is explicitly not enabled by the existing subscription UI.

## Baseline verification executed during this audit

- All **93 PHP files** pass `php -l`.
- `tests/phase2/run_phase2.sh` through `tests/phase6/run_phase6.sh` completed with return code 0 in this audit environment; their static/helper/regression controls passed.
- `tools/secret_scan.py .` passed with no high-confidence embedded production secret or known demo password.
- Historical `tests/phase1/run_baseline.sh` reaches the HTTP/runtime dependency stage but cannot run DB-backed/browser tests here because the audit container has PHP with no PDO MySQL driver. This is an environment limitation, so DB-backed behavior is **not** claimed as runtime-verified in Phase 1.

## Migration decomposition approved by this audit

Proposed Flask layout for later phases:

```text
app.py
config/settings.py
extensions.py
models/
routes/{main,auth,customer,provider,business,admin,billing,api,webhooks}.py
services/{auth,request,notification,upload,billing,razorpay,moderation,search}.py
utils/{helpers,validators,decorators,security,performance}.py
templates/   # mirrors existing page structure
static/      # existing CSS/JS/images retained
scripts/     # admin/reconciliation/config/release/backup helpers
tests/
database/migrations/
docs/
```

## Phase 1 exit criteria

- [x] Entire supplied tree recursively inventoried.
- [x] Current source (not filenames alone) inspected for routes, auth, DB, forms/AJAX, security, uploads, billing and operational scripts.
- [x] Required audit documents created.
- [x] Every current web page/endpoint mapped to a proposed Flask endpoint.
- [x] Effective database schema and migration behavior documented.
- [x] Feature checklist established with migration/test state.
- [x] PHP files/functions mapped to Python/Flask replacements.
- [x] Baseline lint/static/regression tests run; DB-backed/browser limitation recorded rather than hidden.

**Phase 2 may start only from this audited tree and these maps.**
