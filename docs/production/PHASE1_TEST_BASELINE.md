# Phase 1 Test Baseline

Date: 2026-09-24  
Status: baseline established; DB/browser marketplace integration is partially blocked by the audit environment.

## Automated commands

Run from the project root:

```bash
./tests/phase1/run_baseline.sh
python3 tools/phase1_inventory.py
```

## Results in the audit environment

- PHP version: **8.4.23 CLI**
- Original PHP source files linted: **58 / 58 pass**
- Phase 1 helper smoke: **6 checks pass**
- Static security baseline: **9 pass checks, 19 warnings, 0 failed checks**
- Detected POST handlers: **22**
- Detected POST handlers with CSRF validation: **22 / 22**
- Public-page built-in-server smoke: **PASS** for `/localconnect/about.php`
- Observed response headers on that smoke: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`
- Observed session cookie: HttpOnly + SameSite=Lax; not Secure over the HTTP-only local smoke, which is expected for the current implementation
- PDO drivers in this container: **none**; `pdo_mysql` is unavailable
- MySQL/MariaDB service/client: unavailable in this audit container

Therefore the following are **not claimed as executed in Phase 1**:

- SQL migration execution against MySQL/MariaDB
- Real customer/provider/business/admin browser workflows backed by MySQL
- Concurrency/load profiling with seeded marketplace data
- Payment checkout/webhook testing (payment integration does not exist yet)
- Production HTTPS/reverse-proxy behavior

## Static route baseline

The generated `docs/production/route_inventory.csv` records 58 PHP application files/includes. The heuristic classification reports:

- 35 protected/login/role-controlled files
- 2 guest-only auth pages
- 21 public/includes (includes are listed because this is a file inventory, not a claim that every item is a standalone route)
- 22 POST handlers, all with detected CSRF validation
- 32 files calling `fetchAll()`
- 23 static candidates where a file contains `fetchAll()` but no `LIMIT` token; these are review candidates, not automatically defects
- 2 GET logout entry points (`auth/logout.php` and root redirect `logout.php`)

## Baseline security observations tested by automation

Passing checks cover use of `password_verify`, `password_hash`, session ID rotation, disabled PDO emulated prepares, HttpOnly/SameSite session cookie setup, upload MIME/random-name controls, provider plan audience filter, and CSRF presence on detected POST handlers.

Warnings deliberately encode known production gaps so later phases can drive them down: hard-coded DB credentials, missing environment config, business-plan audience bug, disabled checkout/no webhook, demo SQL credentials, destructive fresh SQL, missing login throttling/MFA/password reset/email verification, incomplete image decoding limits, missing HSTS/CSP, GET logout, the three named unbounded request lists, and subscription free-plan concurrency risk.

## Required runtime regression matrix once MySQL/XAMPP or a CI database is available

| Flow | Expected result |
|---|---|
| Customer login → search → provider request | Request created only for authenticated customer and valid provider/service |
| Provider accepts → in progress → completes | Only assigned provider can perform legal transitions |
| Customer review | Only own completed request can be reviewed once |
| Business request flow | Business-owned requests accessible only to that business |
| Open requirement claim | Matching provider/business can claim exactly once |
| Favorites | Customer-only; duplicate favorite prevented |
| Notifications | User can read/mark only own notifications |
| Admin users/verification/moderation | Non-admin receives 403; admin actions require CSRF |
| Blocked user | Existing session no longer grants authenticated platform access |
| Upload negative cases | Non-image, oversized, malformed/oversized-dimension files are rejected after Phase 2 hardening |
| Direct-object tampering | Cross-user request/review/profile mutations are denied |

The Phase 2 test suite should automate these against a disposable MySQL database rather than relying only on manual checks.
