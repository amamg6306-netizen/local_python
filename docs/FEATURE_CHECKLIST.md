# LocalConnect Feature Checklist

> Phase 1 status vocabulary: **AUDITED — MIGRATION PENDING** means the feature exists in the supplied PHP project and has been captured for Flask parity, but has not yet been ported. **BASELINE PASS** means an existing source/static/helper regression was executed successfully. **BLOCKED BY AUDIT ENVIRONMENT** is not a product failure.

> Phase 5 note: functional Flask routes/services now cover all 69 audited legacy web paths with matching HTTP methods. Static parity is verified; DB-backed Flask runtime/browser parity remains pending because the audit container does not have the Flask runtime dependency set installed.
>
> Phase 6 note: the migrated Jinja surface now mirrors the legacy PHP markup/classes/text hierarchy across the critical public, customer, provider, business, admin, and billing pages. All 62 Jinja templates parse; POST forms retain CSRF; literal legacy `.php` links resolve to Flask compatibility routes; AJAX/pagination/static-asset contracts are checked by `tests/python/test_phase6_frontend_parity_static.py` (9/9 PASS). Byte-level comparison against the Phase 5 checkpoint found 0 changes/missing/additions across the 96 tracked original PHP/CSS/JS/image files. Browser/test-client runtime parity remains environment-pending until Flask dependencies are installed.

| Area | Feature / business rule | Existing evidence | Migration status | Current verification |
|---|---|---|---|---|
| Public | Home discovery blocks | index.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Public | Active category directory + service counts | categories.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Public | Search by text/category/location across provider/business/service catalogue | search.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Public | Public provider profile with offered services, portfolio, reviews | provider.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Public | Public business profile with category/services/reviews | business.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Public | About/privacy/terms pages | about.php; privacy.php; terms.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Public | Contact validation-only behavior | contact.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Frontend | Bootstrap/Font Awesome layout and existing CSS | includes/header.php; assets/css/style.css | IMPLEMENTED — PHASE 6 | PASS — Jinja/frontend parity suite; original CSS/assets byte-preserved |
| Frontend | Role-card selection | assets/js/app.js | IMPLEMENTED — PHASE 6 | PASS — existing JavaScript preserved; frontend parity suite |
| Frontend | Category→service filtering | assets/js/app.js | IMPLEMENTED — PHASE 6 | PASS — existing JavaScript preserved; route/form contracts verified |
| Frontend | Confirm-before-submit behavior | assets/js/app.js | IMPLEMENTED — PHASE 6 | PASS — existing JavaScript preserved; syntax/parity checks |
| Frontend | Auto-submit select filters | assets/js/app.js | IMPLEMENTED — PHASE 6 | PASS — existing JavaScript preserved; form route contracts verified |
| Frontend | AJAX favorite toggle and DOM update | assets/js/app.js; ajax/favorite.php | IMPLEMENTED — PHASE 6 | PASS — JSON/AJAX contract + CSRF + route parity verified |
| Auth | Registration roles customer/provider/business | auth/register.php | IMPLEMENTED — PHASE 4 | Phase 4 static parity PASS; runtime suite prepared (dependency install unavailable in audit environment) |
| Auth | Provider/business profile row creation at registration | auth/register.php | IMPLEMENTED — PHASE 4 | Phase 4 static parity PASS; runtime suite prepared (dependency install unavailable in audit environment) |
| Auth | Optional/production-required email verification | auth/register.php; auth/verify-email.php | IMPLEMENTED — PHASE 4 | Phase 4 static parity PASS; runtime suite prepared (dependency install unavailable in audit environment) |
| Auth | Verification resend rate limiting | auth/resend-verification.php | IMPLEMENTED — PHASE 4 | Phase 4 static parity PASS; runtime suite prepared (dependency install unavailable in audit environment) |
| Auth | Login email/password verification + dummy-hash timing mitigation | auth/login.php | IMPLEMENTED — PHASE 4 | Phase 4 static parity PASS; runtime suite prepared (dependency install unavailable in audit environment) |
| Auth | Login rate limiting by email and client-IP HMAC buckets | includes/auth.php | IMPLEMENTED — PHASE 4 | Phase 4 static parity PASS; runtime suite prepared (dependency install unavailable in audit environment) |
| Auth | Blocked/pending account enforcement | auth/login.php; includes/auth.php | IMPLEMENTED — PHASE 4 | Phase 4 static parity PASS; runtime suite prepared (dependency install unavailable in audit environment) |
| Auth | Password rehash on login | auth/login.php | IMPLEMENTED — PHASE 4 | Phase 4 static parity PASS; runtime suite prepared (dependency install unavailable in audit environment) |
| Auth | Session ID regeneration and session_version invalidation | auth/login.php; includes/auth.php | IMPLEMENTED — PHASE 4 | Phase 4 static parity PASS; runtime suite prepared (dependency install unavailable in audit environment) |
| Auth | Idle/absolute session expiry and periodic rotation | includes/auth.php | IMPLEMENTED — PHASE 4 | Phase 4 static parity PASS; runtime suite prepared (dependency install unavailable in audit environment) |
| Auth | POST+CSRF logout | auth/logout.php; logout.php | IMPLEMENTED — PHASE 4 | Phase 4 static parity PASS; runtime suite prepared (dependency install unavailable in audit environment) |
| Auth | Forgot-password opaque response + rate limiting | auth/forgot-password.php | IMPLEMENTED — PHASE 4 | Phase 4 static parity PASS; runtime suite prepared (dependency install unavailable in audit environment) |
| Auth | Hashed selector/token password reset + token invalidation | auth/reset-password.php; includes/functions.php | IMPLEMENTED — PHASE 4 | Phase 4 static parity PASS; runtime suite prepared (dependency install unavailable in audit environment) |
| Auth | Role-based route protection | includes/auth.php | IMPLEMENTED — PHASE 4 | Phase 4 static parity PASS; runtime suite prepared (dependency install unavailable in audit environment) |
| Auth | Admin TOTP MFA setup/verify/replay protection | admin/mfa.php; includes/functions.php | IMPLEMENTED — PHASE 4 | Phase 4 static parity PASS; runtime suite prepared (dependency install unavailable in audit environment) |
| Auth | Recent admin password reauthentication | admin/reauth.php; includes/auth.php | IMPLEMENTED — PHASE 4 | Phase 4 static parity PASS; runtime suite prepared (dependency install unavailable in audit environment) |
| Customer | Customer dashboard | customer/dashboard.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Customer | Direct service request with offered-service validation | request-service.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Customer | Open requirement posting | post-requirement.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Customer | Paginated request history | customer/requests.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Requests | Eligible provider/business requirement feed | provider/available-requirements.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Requests | Atomic claim of open requirement | request-details.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Requests | Server-enforced request state transition matrix | request-details.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Requests | Status-history ledger | request_status_history; request-details.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Requests | Notifications on claim/status changes | request-details.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Requests | Customer cancellation permissions | request-details.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Favorites | Customer saved providers/businesses | favorites.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Favorites | Favorite target must be active provider/business | ajax/favorite.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Reviews | One review per completed request | reviews.php; reviews.request_id UNIQUE | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Reviews | Customer review history | reviews.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Reviews | Provider/business received reviews + rating summary | reviews.php; includes/functions.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Reports | Authenticated user moderation reports | report.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Notifications | Unread counts and notification listing/read state | notifications.php; includes/functions.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Provider | Dashboard counts/profile views/verification state | provider/dashboard.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Provider | Profile/pricing/service-area/availability management | provider/profile.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Provider | Profile image upload/replacement cleanup | provider/profile.php; includes/functions.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Provider | Service offering management | provider/services.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Provider | Portfolio upload/list | provider/portfolio.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Provider | Incoming/claimed request list | provider/requests.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Business | Dashboard | business/dashboard.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Business | Business profile/category/contact/hours/pricing/logo | business/profile.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Business | Service offering management | business/services.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Business | Shared request list | business/requests.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Admin | Dashboard KPIs + recent platform activity | admin/index.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Admin | User role filter + block/unblock; admin self-protection | admin/users.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Admin | Provider verification pending/verified/rejected | admin/providers.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Admin | Business verification pending/verified/rejected | admin/businesses.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Admin | Category create/delete with in-use failure handling | admin/categories.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Admin | Service enable/disable | admin/services.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Admin | Request ledger | admin/requests.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Admin | Review moderation publish/hidden/removed | admin/reviews.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Admin | Report investigation/resolution workflow + notes | admin/reports.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Admin | Advertisement creation/listing/pagination | admin/advertisements.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Admin | Subscription ledger filters/pagination | admin/subscriptions.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Admin | Payment ledger filters/pagination | admin/payments.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Admin | Payment detail/status history/webhook/manual-payment visibility | admin/payment-detail.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Admin | Manual payment verification/rejection with sensitive-auth gates | admin/payment-detail.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Admin | Payment reconciliation/refund/dispute operations | admin/payment-detail.php; includes/billing.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Admin | Payment method listing/configuration indicators/audit | admin/payment-methods.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Admin | Payment method create/edit; allowlisted type/audience/gateway | admin/payment-method-edit.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Admin | Gateway secrets environment-only, never stored in admin method rows | admin/payment-method-edit.php; includes/functions.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Billing | Free subscription bootstrap/current entitlement | includes/functions.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Billing | Role-eligible subscription plans | provider/subscription.php; business/subscription.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Billing | Server-side subtotal/tax/total calculation | includes/billing.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Billing | Checkout intent with hashed token, expiry, plan snapshots | includes/billing.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Billing | Active role/currency-appropriate payment method filtering | includes/functions.php; includes/billing.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Billing | Immutable payment method/plan/instruction snapshots | includes/billing.php; payments schema | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Billing | Razorpay order creation using official API | includes/billing.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Billing | Hosted Razorpay checkout; card data not collected by LocalConnect | billing/gateway.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Billing | Browser callback signature verification without direct entitlement trust | billing/gateway-return.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Billing | Raw-body webhook HMAC + optional IP allowlist + size bound | webhooks/razorpay.php; includes/billing.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Billing | Webhook replay/idempotency event storage | payment_webhook_events schema; includes/billing.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Billing | Server-side remote payment/order reconciliation before paid state | includes/billing.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Billing | Manual UPI/bank reference submission remains pending until admin review | billing/manual.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Billing | Payment status history | payment_status_history schema; includes/billing.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Billing | Subscription entitlement activation/scheduling and benefits | includes/billing.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Billing | Refund/partial refund/dispute handling | includes/billing.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Billing | Bounded reconciliation queue/retry/dead state worker | payment_reconciliation_jobs; tools/payment_reconciliation_worker.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Billing | User billing history | billing/history.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Billing | Checkout/payment cancellation | billing/cancel.php | IMPLEMENTED — PHASE 5 | Phase 5 functional static parity PASS; Flask/DB runtime verification pending dependency-enabled environment |
| Security | CSRF on browser state-changing forms | includes/functions.php; phase2 static test | IMPLEMENTED — PHASE 4/6 | PASS — Flask-WTF CSRF + migrated POST-form static coverage |
| Security | Prepared DB statements / native prepares | config/database.php | IMPLEMENTED — PHASE 3 | PASS — SQLAlchemy/parameterized DB layer + static parity |
| Security | HTML output escaping | includes/functions.php | IMPLEMENTED — PHASE 6 | PASS — Jinja autoescape; no unsafe template escape bypass found |
| Security | CSP nonce + browser/API security headers | includes/security.php | IMPLEMENTED — PHASE 7 | PASS — CSP/HSTS/header static hardening tests |
| Security | Production HTTPS/proxy/HSTS policy | config/app.php; includes/security.php | IMPLEMENTED — PHASE 7 | PASS — production configuration + proxy/header checks |
| Security | Upload MIME/size/dimension/pixel/re-encode/path controls | includes/functions.php | IMPLEMENTED — PHASE 7 | PASS — bounded stream/decode/re-encode/managed-path tests |
| Security | Security logging with scalar redaction | includes/functions.php | IMPLEMENTED — PHASE 7 | PASS — redaction and request-correlation checks |
| Performance | Server-clamped pagination and per+1 sentinel pattern | includes/functions.php; high-growth list routes | IMPLEMENTED — PHASE 5/7 | PASS — bounded-pagination regression suite |
| Performance | Read-heavy session behavior / bounded request state | includes/functions.php; list routes | IMPLEMENTED — PHASE 5/7 | PASS — Flask request-scoped session + bounded-list verification |
| Performance | Request timing/slow-request observability + safe logging | includes/performance.php | IMPLEMENTED — PHASE 7 | PASS — observability/redaction checks |
| Operations | Environment-only production secrets/config | config/app.php; .env.example | IMPLEMENTED — PHASE 2/7 | PASS — secret scan + production config validation |
| Operations | Versioned SQL migrations + preflight + rollback | database/production/* | IMPLEMENTED — PHASE 3 | PASS — migration parser/checksum/preflight tooling |
| Operations | Backup and restore scripts | tools/backup_database.sh; tools/restore_database.sh | RETAINED/AVAILABLE | PASS — scripts retained as operator tooling; no PHP runtime dependency for Flask app |
| Operations | Production config/schema release gates | scripts/check_config.py; scripts/check_db_schema.py | IMPLEMENTED — PHASE 7/9 | PASS — Render pre-deploy gate configured |
| Operations | Dependency inventory and secret scanner | tools/dependency_inventory.py; tools/secret_scan.py | IMPLEMENTED/RETAINED | PASS — final supply-chain inventory + secret scan |
| Testing | All PHP syntax | 93 PHP files | BASELINE PASS | php -l 93/93 |
| Testing | Phase 2–6 static/helper/regression suites | tests/phase2..phase6 | BASELINE PASS | All run scripts RC=0 in audit container |
| Testing | DB-backed/browser runtime baseline | tests/phase1/http_header_smoke.sh | BLOCKED BY AUDIT ENVIRONMENT | PHP PDO MySQL driver unavailable; not claimed |

## Route-by-route migration coverage

| Existing route | Purpose | Migration | Test |
|---|---|---|---|
| `/403.php` | Access-denied page/handler | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/404.php` | Not-found page/handler | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/index.php` | Home page: categories, featured providers, businesses, search CTA | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/about.php` | About page | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/privacy.php` | Privacy page | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/terms.php` | Terms page | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/categories.php` | Active category directory with service counts | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/search.php` | Provider/business/service search with category/location filters and pagination | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/provider.php` | Public provider profile, services, portfolio, reviews, favorite/request actions | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/business.php` | Public business profile, services, reviews, favorite/request actions | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/contact.php` | Contact form validation; current source intentionally does not deliver/persist message | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/favorites.php` | Paginated saved provider/business list | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/notifications.php` | Notification list and read-state updates | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/reviews.php` | Customer review creation/history and provider/business received reviews | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/report.php` | Create moderation report against provider/business/review | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/post-requirement.php` | Create open requirement matched by service | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/request-service.php` | Create direct provider/business service request | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/request-details.php` | Request detail, claim flow, allowed status transitions, history, notifications | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/login.php` | Legacy redirect to auth/login.php | ☑ implemented | ◐ static PASS / runtime pending |
| `/logout.php` | Legacy POST+CSRF logout | ☑ implemented | ◐ static PASS / runtime pending |
| `/register.php` | Legacy redirect to auth/register.php | ☑ implemented | ◐ static PASS / runtime pending |
| `/auth/login.php` | Login, throttling, password rehash, session rotation, admin-MFA redirect | ☑ implemented | ◐ static PASS / runtime pending |
| `/auth/logout.php` | POST+CSRF logout and session destruction | ☑ implemented | ◐ static PASS / runtime pending |
| `/auth/register.php` | Customer/provider/business registration and role-profile creation | ☑ implemented | ◐ static PASS / runtime pending |
| `/auth/forgot-password.php` | Password reset request with rate limiting and opaque response | ☑ implemented | ◐ static PASS / runtime pending |
| `/auth/reset-password.php` | Selector/token reset flow; rotates session_version | ☑ implemented | ◐ static PASS / runtime pending |
| `/auth/resend-verification.php` | Email-verification resend with rate limiting | ☑ implemented | ◐ static PASS / runtime pending |
| `/auth/verify-email.php` | Consume email-verification token and activate pending user | ☑ implemented | ◐ static PASS / runtime pending |
| `/customer/dashboard.php` | Customer dashboard and quick actions | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/customer/requests.php` | Paginated direct/open request history | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/provider/dashboard.php` | Provider stats and management shortcuts | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/provider/profile.php` | Provider profile/location/pricing/availability + profile-image upload | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/provider/services.php` | Provider service offering create/delete listing management | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/provider/portfolio.php` | Portfolio image upload and paginated gallery | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/provider/requests.php` | Shared incoming/claimed request list | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/provider/available-requirements.php` | Open requirements matched to active offered services | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/provider/subscription.php` | Provider plan catalogue/current entitlement and checkout entry | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/business/dashboard.php` | Business dashboard and profile/service shortcuts | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/business/profile.php` | Business identity/category/contact/hours/pricing/logo profile management | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/business/services.php` | Business service offering management | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/business/requests.php` | Business alias of shared provider/business request list | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/business/subscription.php` | Business plan catalogue/current entitlement and checkout entry | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/ajax/favorite.php` | JSON favorite toggle with CSRF and target validation | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/billing/start.php` | Server-side plan validation and checkout-intent creation | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/billing/payment-method.php` | Role/currency-filtered active payment method chooser | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/billing/select-method.php` | Payment record creation with immutable method/plan snapshots | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/billing/gateway.php` | Razorpay hosted checkout bootstrap | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/billing/gateway-return.php` | Browser callback signature validation; no trust-based entitlement | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/billing/manual.php` | UPI/bank instructions and transfer-reference submission | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/billing/history.php` | Paginated payment/subscription history | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/billing/cancel.php` | Cancel eligible checkout/payment state | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/webhooks/razorpay.php` | Razorpay raw-body webhook verification, replay protection and reconciliation | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/admin/index.php` | Admin KPI dashboard and recent platform activity | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/admin/users.php` | Role filter; block/unblock non-admin users and invalidate sessions | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/admin/providers.php` | Provider verification moderation | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/admin/businesses.php` | Business verification moderation | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/admin/categories.php` | Category create/delete and validation | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/admin/services.php` | Paginated service activation toggle | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/admin/requests.php` | Administrative service-request ledger | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/admin/reviews.php` | Review publish/hide/remove moderation | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/admin/reports.php` | Report workflow open/investigating/resolved/dismissed with notes | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/admin/advertisements.php` | Advertisement creation/listing with placement/status/date/budget validation | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/admin/subscriptions.php` | Subscription ledger with status/plan/text filters and pagination | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/admin/payments.php` | Payment ledger/filtering/pagination | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/admin/payment-detail.php` | Payment history/webhook/manual details; verification/reconciliation/refund/dispute operations | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/admin/payment-methods.php` | Payment-method listing, configuration status and audit trail | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/admin/payment-method-edit.php` | Create/edit allowed gateway/UPI/bank method metadata; secrets remain environment-only | ☑ implemented | ◐ static PASS / Flask runtime pending |
| `/admin/mfa.php` | TOTP setup/verify/optional-disable according to policy | ☑ implemented | ◐ static PASS / runtime pending |
| `/admin/reauth.php` | Password reconfirmation for sensitive admin actions | ☑ implemented | ◐ static PASS / runtime pending |

## Completion rule

A required row may be changed to **PASS** only after its Flask implementation exists and the corresponding automated/manual parity test passes. Phase 1 intentionally leaves route migration boxes unchecked. No original required feature may remain FAIL when the overall project is declared complete.

## Python migration infrastructure status

| Migration foundation | Status | Verification |
|---|---|---|
| Flask application/config foundation | PASS | Phase 2 Python source/static verification; runtime dependency install still required in an environment with package access |
| Effective MySQL/MariaDB schema mapped to SQLAlchemy | PASS | 32/32 tables and 365 effective columns matched by `tests/python/test_phase3_database_static.py` |
| Named indexes/unique constraints/foreign-key/check names mapped | PASS | Static metadata-source parity check |
| Canonical fresh schema alias | PASS | `database/schema.sql` SHA-256 matches `database/production/fresh_schema.sql` |
| Existing-database migration runner | PASS | Forward migration discovery, checksum guard, preflight support, custom database-name safety |
| Empty-database initializer safety | PASS | Refuses initialization when base tables already exist |
| Live database schema checker | READY — ENVIRONMENT PENDING | Requires configured external MySQL/MariaDB credentials |
| Flask/SQLAlchemy runtime database test | READY — DEPENDENCY ENVIRONMENT PENDING | Workspace lacks installed Flask/SQLAlchemy packages; test file is included for execution after dependency installation |

## Phase 7 production infrastructure status

| Production concern | Status | Verification |
|---|---|---|
| Persistent user-upload storage | PASS — CODE/BLUEPRINT | Configurable filesystem root; Render disk mounted at `/var/data/localconnect/uploads`; legacy DB paths preserved |
| Upload stream/file hardening | PASS — STATIC | Bounded stream copy, MIME/image decoding, dimensions/pixel cap, metadata-stripping re-encode, random server names, managed-path allowlist |
| Legacy upload migration | PASS — STATIC | Non-overwriting idempotent `scripts/sync_uploads_to_storage.py` |
| Production request limits | PASS — STATIC | Request bytes, multipart memory and form-part caps configured |
| Host/proxy/HTTPS policy | PASS — STATIC | HTTPS/HSTS/CSP retained; trusted host derived from `APP_URL`; explicit proxy policy retained |
| Production logging/traceability | PASS — STATIC | Secret redaction plus Render `Rndr-Id` and Cloudflare `CF-Ray` correlation; slow-request timing |
| Render Native Python blueprint | PASS — STATIC | Python runtime, Gunicorn, `/health`, persistent disk, no Docker |
| Live persistent-disk runtime check | READY — DEPLOYMENT PENDING | Startup performs a write probe; requires actual Render runtime |

## Phase 8 verification status

| Verification concern | Status | Verification |
|---|---|---|
| Python source compile | PASS | `python -m compileall` across app/config/database/models/routes/services/utils/scripts |
| Jinja template parse | PASS | 62/62 templates parse |
| Model-field reference consistency | PASS | Phase 8 AST model-reference gate found 0 unknown fields |
| Template context contracts | PASS | Direct `render_template()` contexts satisfy template undeclared-variable requirements |
| Form/fetch route contracts | PASS | Literal form actions/methods and fetch targets resolve to Flask routes |
| JavaScript syntax | PASS | `node --check assets/js/app.js` |
| MySQL migration parser | PASS | 25 SQL files / 490 statements parsed |
| Secret scan | PASS | No high-confidence embedded production secrets/demo passwords |
| Request status concurrency | PASS — FIXED | Status transition now uses row lock and revalidates ownership/allowed transition inside transaction |
| Legacy PHP regression suites | PASS — STATIC/HELPERS | Phase 2–6 regression assertions pass; DB/browser portions remain environment-gated |
| Frontend byte parity vs pre-Phase-8 | PASS | 0 changed / 0 missing / 0 added tracked PHP/CSS/JS/image files |
| Flask runtime test suite | READY — DEPENDENCY ENVIRONMENT PENDING | 83 tests pass + 20 dependency/runtime-gated skips + 18 subtests pass in this workspace; 0 failures |
| Live MySQL end-to-end | READY — ENVIRONMENT PENDING | Requires installed runtime dependencies and configured external MySQL/MariaDB |
