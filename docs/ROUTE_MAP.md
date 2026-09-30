# LocalConnect Route Map

> Phase 1 audit output. The migration strategy is **URL-preserving first**: Flask will expose the same `.php` paths as compatibility/canonical routes so existing links, bookmarks and JavaScript continue to work even though no PHP runtime exists. Internal Flask endpoint names are shown below. Clean aliases may be added later only if they do not break parity.

Current web route/page files mapped: **69**. `admin/_nav.php` is a template partial and is mapped separately.

| Existing path | Methods | Current access rule | Proposed Flask endpoint | Behavior to preserve |
|---|---|---|---|---|
| `/403.php` | GET | public | `errors.forbidden` at `/403.php` | Access-denied page/handler |
| `/404.php` | GET | public | `errors.not_found` at `/404.php` | Not-found page/handler |
| `/index.php` | GET | public | `main.index` at `/index.php` | Home page: categories, featured providers, businesses, search CTA |
| `/about.php` | GET | public | `main.about` at `/about.php` | About page |
| `/privacy.php` | GET | public | `main.privacy` at `/privacy.php` | Privacy page |
| `/terms.php` | GET | public | `main.terms` at `/terms.php` | Terms page |
| `/categories.php` | GET | public | `main.categories` at `/categories.php` | Active category directory with service counts |
| `/search.php` | GET | public | `main.search` at `/search.php` | Provider/business/service search with category/location filters and pagination |
| `/provider.php` | GET | public | `main.provider_detail` at `/provider.php` | Public provider profile, services, portfolio, reviews, favorite/request actions |
| `/business.php` | GET | public | `main.business_detail` at `/business.php` | Public business profile, services, reviews, favorite/request actions |
| `/contact.php` | GET,POST | public | `main.contact` at `/contact.php` | Contact form validation; current source intentionally does not deliver/persist message |
| `/favorites.php` | GET | customer | `customer.favorites` at `/favorites.php` | Paginated saved provider/business list |
| `/notifications.php` | GET,POST | authenticated | `main.notifications` at `/notifications.php` | Notification list and read-state updates |
| `/reviews.php` | GET,POST | authenticated | `main.reviews` at `/reviews.php` | Customer review creation/history and provider/business received reviews |
| `/report.php` | GET,POST | authenticated | `main.report` at `/report.php` | Create moderation report against provider/business/review |
| `/post-requirement.php` | GET,POST | customer | `customer.post_requirement` at `/post-requirement.php` | Create open requirement matched by service |
| `/request-service.php` | GET,POST | customer | `customer.request_service` at `/request-service.php` | Create direct provider/business service request |
| `/request-details.php` | GET,POST | authenticated participant / eligible provider-business claimant | `main.request_details` at `/request-details.php` | Request detail, claim flow, allowed status transitions, history, notifications |
| `/login.php` | GET | public compatibility | `auth.login_legacy` at `/login.php` | Legacy redirect to auth/login.php |
| `/logout.php` | POST | authenticated compatibility | `auth.logout_legacy` at `/logout.php` | Legacy POST+CSRF logout |
| `/register.php` | GET | public compatibility | `auth.register_legacy` at `/register.php` | Legacy redirect to auth/register.php |
| `/auth/login.php` | GET,POST | guest-only | `auth.login` at `/auth/login.php` | Login, throttling, password rehash, session rotation, admin-MFA redirect |
| `/auth/logout.php` | POST | authenticated | `auth.logout` at `/auth/logout.php` | POST+CSRF logout and session destruction |
| `/auth/register.php` | GET,POST | guest-only | `auth.register` at `/auth/register.php` | Customer/provider/business registration and role-profile creation |
| `/auth/forgot-password.php` | GET,POST | guest-only | `auth.forgot_password` at `/auth/forgot-password.php` | Password reset request with rate limiting and opaque response |
| `/auth/reset-password.php` | GET,POST | guest-only | `auth.reset_password` at `/auth/reset-password.php` | Selector/token reset flow; rotates session_version |
| `/auth/resend-verification.php` | GET,POST | guest-only | `auth.resend_verification` at `/auth/resend-verification.php` | Email-verification resend with rate limiting |
| `/auth/verify-email.php` | GET | token-authenticated | `auth.verify_email` at `/auth/verify-email.php` | Consume email-verification token and activate pending user |
| `/customer/dashboard.php` | GET | customer | `customer.dashboard` at `/customer/dashboard.php` | Customer dashboard and quick actions |
| `/customer/requests.php` | GET | customer | `customer.requests` at `/customer/requests.php` | Paginated direct/open request history |
| `/provider/dashboard.php` | GET | provider | `provider.dashboard` at `/provider/dashboard.php` | Provider stats and management shortcuts |
| `/provider/profile.php` | GET,POST | provider | `provider.profile` at `/provider/profile.php` | Provider profile/location/pricing/availability + profile-image upload |
| `/provider/services.php` | GET,POST | provider | `provider.services` at `/provider/services.php` | Provider service offering create/delete listing management |
| `/provider/portfolio.php` | GET,POST | provider | `provider.portfolio` at `/provider/portfolio.php` | Portfolio image upload and paginated gallery |
| `/provider/requests.php` | GET | provider or business | `provider.requests` at `/provider/requests.php` | Shared incoming/claimed request list |
| `/provider/available-requirements.php` | GET | provider or business | `provider.available_requirements` at `/provider/available-requirements.php` | Open requirements matched to active offered services |
| `/provider/subscription.php` | GET | provider | `provider.subscription` at `/provider/subscription.php` | Provider plan catalogue/current entitlement and checkout entry |
| `/business/dashboard.php` | GET | business | `business.dashboard` at `/business/dashboard.php` | Business dashboard and profile/service shortcuts |
| `/business/profile.php` | GET,POST | business | `business.profile` at `/business/profile.php` | Business identity/category/contact/hours/pricing/logo profile management |
| `/business/services.php` | GET,POST | business | `business.services` at `/business/services.php` | Business service offering management |
| `/business/requests.php` | GET | business | `business.requests` at `/business/requests.php` | Business alias of shared provider/business request list |
| `/business/subscription.php` | GET | business | `business.subscription` at `/business/subscription.php` | Business plan catalogue/current entitlement and checkout entry |
| `/ajax/favorite.php` | POST | customer | `api.favorite` at `/ajax/favorite.php` | JSON favorite toggle with CSRF and target validation |
| `/billing/start.php` | POST | provider or business | `billing.start` at `/billing/start.php` | Server-side plan validation and checkout-intent creation |
| `/billing/payment-method.php` | GET | provider or business | `billing.payment_method` at `/billing/payment-method.php` | Role/currency-filtered active payment method chooser |
| `/billing/select-method.php` | POST | provider or business | `billing.select_method` at `/billing/select-method.php` | Payment record creation with immutable method/plan snapshots |
| `/billing/gateway.php` | GET | provider or business | `billing.gateway` at `/billing/gateway.php` | Razorpay hosted checkout bootstrap |
| `/billing/gateway-return.php` | POST | provider or business | `billing.gateway_return` at `/billing/gateway-return.php` | Browser callback signature validation; no trust-based entitlement |
| `/billing/manual.php` | GET,POST | provider or business | `billing.manual` at `/billing/manual.php` | UPI/bank instructions and transfer-reference submission |
| `/billing/history.php` | GET | provider or business | `billing.history` at `/billing/history.php` | Paginated payment/subscription history |
| `/billing/cancel.php` | POST | provider or business | `billing.cancel` at `/billing/cancel.php` | Cancel eligible checkout/payment state |
| `/webhooks/razorpay.php` | POST | server-to-server HMAC/IP policy | `webhooks.razorpay` at `/webhooks/razorpay.php` | Razorpay raw-body webhook verification, replay protection and reconciliation |
| `/admin/index.php` | GET | admin + MFA | `admin.dashboard` at `/admin/index.php` | Admin KPI dashboard and recent platform activity |
| `/admin/users.php` | GET,POST | admin + MFA | `admin.users` at `/admin/users.php` | Role filter; block/unblock non-admin users and invalidate sessions |
| `/admin/providers.php` | GET,POST | admin + MFA | `admin.providers` at `/admin/providers.php` | Provider verification moderation |
| `/admin/businesses.php` | GET,POST | admin + MFA | `admin.businesses` at `/admin/businesses.php` | Business verification moderation |
| `/admin/categories.php` | GET,POST | admin + MFA | `admin.categories` at `/admin/categories.php` | Category create/delete and validation |
| `/admin/services.php` | GET,POST | admin + MFA | `admin.services` at `/admin/services.php` | Paginated service activation toggle |
| `/admin/requests.php` | GET | admin + MFA | `admin.requests` at `/admin/requests.php` | Administrative service-request ledger |
| `/admin/reviews.php` | GET,POST | admin + MFA | `admin.reviews` at `/admin/reviews.php` | Review publish/hide/remove moderation |
| `/admin/reports.php` | GET,POST | admin + MFA | `admin.reports` at `/admin/reports.php` | Report workflow open/investigating/resolved/dismissed with notes |
| `/admin/advertisements.php` | GET,POST | admin + MFA | `admin.advertisements` at `/admin/advertisements.php` | Advertisement creation/listing with placement/status/date/budget validation |
| `/admin/subscriptions.php` | GET | admin + MFA | `admin.subscriptions` at `/admin/subscriptions.php` | Subscription ledger with status/plan/text filters and pagination |
| `/admin/payments.php` | GET | admin + MFA | `admin.payments` at `/admin/payments.php` | Payment ledger/filtering/pagination |
| `/admin/payment-detail.php` | GET,POST | admin + MFA + recent reauth for sensitive actions | `admin.payment_detail` at `/admin/payment-detail.php` | Payment history/webhook/manual details; verification/reconciliation/refund/dispute operations |
| `/admin/payment-methods.php` | GET | admin + MFA | `admin.payment_methods` at `/admin/payment-methods.php` | Payment-method listing, configuration status and audit trail |
| `/admin/payment-method-edit.php` | GET,POST | admin + MFA + recent reauth | `admin.payment_method_edit` at `/admin/payment-method-edit.php` | Create/edit allowed gateway/UPI/bank method metadata; secrets remain environment-only |
| `/admin/mfa.php` | GET,POST | admin login | `admin.mfa` at `/admin/mfa.php` | TOTP setup/verify/optional-disable according to policy |
| `/admin/reauth.php` | GET,POST | admin + MFA | `admin.reauth` at `/admin/reauth.php` | Password reconfirmation for sensitive admin actions |

## Non-routable PHP page partial

| Existing file | Flask replacement |
|---|---|
| `admin/_nav.php` | `templates/admin/_nav.html` included by admin templates |

## .htaccess behavior that must move into Flask/Render

- `DirectoryIndex index.php` → Flask `/` route serves the home page directly.
- Custom 404 → Flask `@app.errorhandler(404)` rendering the migrated 404 template.
- Source/config/backup file denial → files are not placed under Flask static roots; deployment layout prevents direct serving.
- Security headers → Flask `after_request`/security middleware; do not depend on Apache `mod_headers`.
- `Options -Indexes -MultiViews` → no directory browsing; explicit Flask routes only.
- Existing base path `/localconnect/` is environment-configurable and must be reflected by routing/proxy configuration.

## Route parity rule

Every row above must later be marked implemented/tested in `FEATURE_CHECKLIST.md`. No legacy path may become an accidental 404. POST-only routes keep their method restrictions and CSRF/auth semantics.
