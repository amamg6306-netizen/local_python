# Phase 2 state-changing route coverage

Static coverage inventory only; ownership/state-transition checks still require DB-backed integration tests.

| Route | Auth gate | CSRF |
|---|---|---|
| `admin/advertisements.php` | admin | yes |
| `admin/businesses.php` | admin | yes |
| `admin/categories.php` | admin | yes |
| `admin/mfa.php` | login | yes |
| `admin/providers.php` | admin | yes |
| `admin/reauth.php` | login | yes |
| `admin/reports.php` | admin | yes |
| `admin/reviews.php` | admin | yes |
| `admin/services.php` | admin | yes |
| `admin/users.php` | admin | yes |
| `auth/forgot-password.php` | guest/public | yes |
| `auth/login.php` | guest/public | yes |
| `auth/logout.php` | guest/public | yes |
| `auth/register.php` | guest/public | yes |
| `auth/resend-verification.php` | guest/public | yes |
| `auth/reset-password.php` | guest/public | yes |
| `business/profile.php` | role | yes |
| `business/services.php` | role | yes |
| `contact.php` | guest/public | yes |
| `logout.php` | guest/public | yes |
| `notifications.php` | login | yes |
| `post-requirement.php` | role | yes |
| `provider/portfolio.php` | role | yes |
| `provider/profile.php` | role | yes |
| `provider/services.php` | role | yes |
| `report.php` | login | yes |
| `request-details.php` | login | yes |
| `request-service.php` | role | yes |
| `reviews.php` | login | yes |

**Detected handlers: 29; CSRF covered: 29/29.**
