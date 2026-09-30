# LocalConnect Database Map

> Source of truth for the target migration is the supplied MySQL/MariaDB schema. The canonical fresh-install snapshot is `database/production/fresh_schema.sql`; historical and production migrations remain important for upgrading existing data safely.

**Tables discovered: 32. SQL files audited: 24.**

## Database configuration and compatibility

- Driver today: PHP PDO/MySQL with native prepares (`ATTR_EMULATE_PREPARES=false`).
- Required migration target: external MySQL/MariaDB, environment-driven credentials, parameterized SQL/SQLAlchemy/PyMySQL.
- Current variables: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASS`. The Python migration should accept `DB_PASSWORD` as the preferred name and may support `DB_PASS` as a temporary compatibility alias.
- Fresh schema contains seed categories, services and subscription plans. No production credentials are embedded.
- Existing migration design includes forward migrations, preflight files, rollback files and `schema_migrations`; these semantics must not be replaced by destructive recreate-on-start behavior.

## Effective schema

### `users`

| Column | Definition |
|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` |
| `name` | `VARCHAR(120) NOT NULL` |
| `email` | `VARCHAR(190) NOT NULL UNIQUE` |
| `phone` | `VARCHAR(25) NULL` |
| `password_hash` | `VARCHAR(255) NOT NULL` |
| `role` | `ENUM('customer','provider','business','admin') NOT NULL DEFAULT 'customer'` |
| `status` | `ENUM('active','blocked','pending') NOT NULL DEFAULT 'active'` |
| `profile_image` | `VARCHAR(255) NULL` |
| `city` | `VARCHAR(100) NULL` |
| `state` | `VARCHAR(100) NULL` |
| `area` | `VARCHAR(150) NULL` |
| `pincode` | `VARCHAR(12) NULL` |
| `latitude` | `DECIMAL(10,7) NULL` |
| `longitude` | `DECIMAL(10,7) NULL` |
| `last_login_at` | `DATETIME NULL` |
| `email_verified_at` | `DATETIME NULL` |
| `session_version` | `INT UNSIGNED NOT NULL DEFAULT 1` |
| `created_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` |

**Keys / constraints declared at creation**

- `INDEX idx_users_role_status(role,status)`
- `INDEX idx_users_location(city,state,area)`
- `INDEX idx_users_name(name)`

**Post-create migration additions**

- `INDEX idx_users_role_status_id(role,status,id)`

**Application usage:** `admin/_nav.php`, `admin/businesses.php`, `admin/index.php`, `admin/mfa.php`, `admin/payment-detail.php`, `admin/payment-methods.php`, `admin/payments.php`, `admin/providers.php`, `admin/reauth.php`, `admin/reports.php`, `admin/requests.php`, `admin/reviews.php`, `admin/subscriptions.php`, `admin/users.php`, `ajax/favorite.php`, `auth/forgot-password.php`, `auth/login.php`, `auth/register.php` …

### `locations`

| Column | Definition |
|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` |
| `user_id` | `BIGINT UNSIGNED NOT NULL` |
| `label` | `VARCHAR(80) DEFAULT 'Primary'` |
| `address_line` | `VARCHAR(255) NULL` |
| `area` | `VARCHAR(150) NULL` |
| `city` | `VARCHAR(100) NOT NULL` |
| `state` | `VARCHAR(100) NOT NULL` |
| `pincode` | `VARCHAR(12) NULL` |
| `latitude` | `DECIMAL(10,7) NULL` |
| `longitude` | `DECIMAL(10,7) NULL` |
| `is_default` | `TINYINT(1) NOT NULL DEFAULT 0` |
| `created_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` |

**Keys / constraints declared at creation**

- `CONSTRAINT fk_locations_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE`
- `INDEX idx_locations_city(city,state,area)`

**Application usage:** No direct production-PHP reference found.

### `categories`

| Column | Definition |
|---|---|
| `id` | `INT UNSIGNED AUTO_INCREMENT PRIMARY KEY` |
| `name` | `VARCHAR(120) NOT NULL UNIQUE` |
| `slug` | `VARCHAR(140) NOT NULL UNIQUE` |
| `icon` | `VARCHAR(80) NULL` |
| `description` | `VARCHAR(255) NULL` |
| `is_active` | `TINYINT(1) NOT NULL DEFAULT 1` |
| `created_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` |

**Keys / constraints declared at creation**

- `INDEX idx_categories_active(is_active)`

**Application usage:** `admin/_nav.php`, `admin/categories.php`, `admin/requests.php`, `admin/services.php`, `business.php`, `business/profile.php`, `business/services.php`, `categories.php`, `customer/requests.php`, `includes/footer.php`, `includes/navbar.php`, `index.php`, `post-requirement.php`, `provider.php`, `provider/available-requirements.php`, `provider/requests.php`, `provider/services.php`, `request-details.php` …

### `provider_profiles`

| Column | Definition |
|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` |
| `user_id` | `BIGINT UNSIGNED NOT NULL UNIQUE` |
| `headline` | `VARCHAR(180) NULL` |
| `about` | `TEXT NULL` |
| `experience_years` | `SMALLINT UNSIGNED DEFAULT 0` |
| `service_area` | `VARCHAR(255) NULL` |
| `price_min` | `DECIMAL(10,2) NULL` |
| `price_max` | `DECIMAL(10,2) NULL` |
| `availability_status` | `ENUM('available','busy','unavailable') NOT NULL DEFAULT 'available'` |
| `working_hours` | `VARCHAR(255) NULL` |
| `verification_status` | `ENUM('pending','verified','rejected') NOT NULL DEFAULT 'pending'` |
| `verified_at` | `DATETIME NULL` |
| `is_featured` | `TINYINT(1) NOT NULL DEFAULT 0` |
| `profile_views` | `INT UNSIGNED NOT NULL DEFAULT 0` |
| `created_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` |

**Keys / constraints declared at creation**

- `CONSTRAINT fk_provider_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE`
- `INDEX idx_provider_verify(verification_status)`
- `INDEX idx_provider_available(availability_status)`

**Application usage:** `admin/index.php`, `admin/providers.php`, `auth/register.php`, `favorites.php`, `index.php`, `provider.php`, `provider/dashboard.php`, `provider/profile.php`, `search.php`, `tools/performance_seed.php`

### `business_profiles`

| Column | Definition |
|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` |
| `user_id` | `BIGINT UNSIGNED NOT NULL UNIQUE` |
| `category_id` | `INT UNSIGNED NULL` |
| `business_name` | `VARCHAR(180) NULL` |
| `slug` | `VARCHAR(200) NULL UNIQUE` |
| `logo` | `VARCHAR(255) NULL` |
| `description` | `TEXT NULL` |
| `address` | `VARCHAR(255) NULL` |
| `phone` | `VARCHAR(25) NULL` |
| `opening_time` | `TIME NULL` |
| `closing_time` | `TIME NULL` |
| `price_min` | `DECIMAL(10,2) NULL` |
| `price_max` | `DECIMAL(10,2) NULL` |
| `website` | `VARCHAR(255) NULL` |
| `social_links` | `JSON NULL` |
| `verification_status` | `ENUM('pending','verified','rejected') NOT NULL DEFAULT 'pending'` |
| `verified_at` | `DATETIME NULL` |
| `is_featured` | `TINYINT(1) NOT NULL DEFAULT 0` |
| `profile_views` | `INT UNSIGNED NOT NULL DEFAULT 0` |
| `created_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` |

**Keys / constraints declared at creation**

- `CONSTRAINT fk_business_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE`
- `CONSTRAINT fk_business_category FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE SET NULL`
- `INDEX idx_business_name(business_name)`
- `INDEX idx_business_verify(verification_status)`

**Application usage:** `admin/businesses.php`, `admin/index.php`, `auth/register.php`, `business.php`, `business/dashboard.php`, `business/profile.php`, `favorites.php`, `index.php`, `search.php`

### `services`

| Column | Definition |
|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` |
| `category_id` | `INT UNSIGNED NOT NULL` |
| `name` | `VARCHAR(160) NOT NULL` |
| `slug` | `VARCHAR(180) NOT NULL` |
| `description` | `TEXT NULL` |
| `is_active` | `TINYINT(1) NOT NULL DEFAULT 1` |
| `created_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` |

**Keys / constraints declared at creation**

- `CONSTRAINT fk_services_category FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE RESTRICT`
- `UNIQUE KEY uq_service_category_slug(category_id,slug)`
- `INDEX idx_service_name(name)`

**Application usage:** `about.php`, `admin/_nav.php`, `admin/services.php`, `auth/register.php`, `business.php`, `business/dashboard.php`, `business/services.php`, `categories.php`, `customer/dashboard.php`, `customer/requests.php`, `favorites.php`, `includes/footer.php`, `includes/navbar.php`, `index.php`, `post-requirement.php`, `provider.php`, `provider/available-requirements.php`, `provider/dashboard.php` …

### `provider_services`

| Column | Definition |
|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` |
| `provider_user_id` | `BIGINT UNSIGNED NOT NULL` |
| `service_id` | `BIGINT UNSIGNED NOT NULL` |
| `title` | `VARCHAR(180) NULL` |
| `description` | `TEXT NULL` |
| `price_from` | `DECIMAL(10,2) NULL` |
| `price_to` | `DECIMAL(10,2) NULL` |
| `is_active` | `TINYINT(1) NOT NULL DEFAULT 1` |
| `created_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` |

**Keys / constraints declared at creation**

- `CONSTRAINT fk_ps_user FOREIGN KEY(provider_user_id) REFERENCES users(id) ON DELETE CASCADE`
- `CONSTRAINT fk_ps_service FOREIGN KEY(service_id) REFERENCES services(id) ON DELETE CASCADE`
- `UNIQUE KEY uq_provider_service(provider_user_id,service_id)`
- `INDEX idx_ps_active(is_active)`

**Application usage:** `business.php`, `business/dashboard.php`, `business/services.php`, `provider.php`, `provider/available-requirements.php`, `provider/dashboard.php`, `provider/services.php`, `request-details.php`, `request-service.php`, `search.php`, `tools/performance_seed.php`

### `portfolio_images`

| Column | Definition |
|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` |
| `user_id` | `BIGINT UNSIGNED NOT NULL` |
| `image_path` | `VARCHAR(255) NOT NULL` |
| `caption` | `VARCHAR(255) NULL` |
| `created_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` |

**Keys / constraints declared at creation**

- `CONSTRAINT fk_portfolio_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE`
- `INDEX idx_portfolio_user(user_id,created_at)`

**Post-create migration additions**

- `INDEX idx_portfolio_user_created_id(user_id,created_at,id)`

**Application usage:** `provider.php`, `provider/dashboard.php`, `provider/portfolio.php`

### `service_requests`

| Column | Definition |
|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` |
| `customer_id` | `BIGINT UNSIGNED NOT NULL` |
| `provider_id` | `BIGINT UNSIGNED NULL` |
| `business_id` | `BIGINT UNSIGNED NULL` |
| `category_id` | `INT UNSIGNED NOT NULL` |
| `service_id` | `BIGINT UNSIGNED NULL` |
| `request_type` | `ENUM('direct','requirement') NOT NULL DEFAULT 'direct'` |
| `title` | `VARCHAR(180) NOT NULL` |
| `description` | `TEXT NOT NULL` |
| `location_text` | `VARCHAR(255) NOT NULL` |
| `preferred_date` | `DATE NULL` |
| `preferred_time` | `TIME NULL` |
| `budget_min` | `DECIMAL(10,2) NULL` |
| `budget_max` | `DECIMAL(10,2) NULL` |
| `additional_notes` | `TEXT NULL` |
| `status` | `ENUM('pending','accepted','rejected','in_progress','completed','cancelled') NOT NULL DEFAULT 'pending'` |
| `created_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` |

**Keys / constraints declared at creation**

- `CONSTRAINT fk_sr_customer FOREIGN KEY(customer_id) REFERENCES users(id) ON DELETE CASCADE`
- `CONSTRAINT fk_sr_provider FOREIGN KEY(provider_id) REFERENCES users(id) ON DELETE SET NULL`
- `CONSTRAINT fk_sr_business FOREIGN KEY(business_id) REFERENCES users(id) ON DELETE SET NULL`
- `CONSTRAINT fk_sr_category FOREIGN KEY(category_id) REFERENCES categories(id)`
- `CONSTRAINT fk_sr_service FOREIGN KEY(service_id) REFERENCES services(id) ON DELETE SET NULL`
- `INDEX idx_sr_status(status)`
- `INDEX idx_sr_provider(provider_id,status)`
- `INDEX idx_sr_customer(customer_id,status)`
- `INDEX idx_sr_category(category_id,status)`
- `INDEX idx_sr_type_status_service(request_type,status,service_id)`
- `INDEX idx_sr_business(business_id,status)`

**Post-create migration additions**

- `INDEX idx_sr_provider_created(provider_id,created_at,id)`
- `INDEX idx_sr_business_created(business_id,created_at,id)`
- `INDEX idx_sr_customer_created(customer_id,created_at,id)`
- `INDEX idx_sr_requirement_feed(request_type,status,created_at,id,service_id)`

**Application usage:** `admin/index.php`, `admin/requests.php`, `customer/requests.php`, `post-requirement.php`, `provider/available-requirements.php`, `provider/requests.php`, `request-details.php`, `request-service.php`, `reviews.php`, `tools/performance_seed.php`

### `request_status_history`

| Column | Definition |
|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` |
| `request_id` | `BIGINT UNSIGNED NOT NULL` |
| `status` | `ENUM('pending','accepted','rejected','in_progress','completed','cancelled') NOT NULL` |
| `changed_by` | `BIGINT UNSIGNED NOT NULL` |
| `note` | `VARCHAR(500) NULL` |
| `created_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` |

**Keys / constraints declared at creation**

- `CONSTRAINT fk_rsh_request FOREIGN KEY(request_id) REFERENCES service_requests(id) ON DELETE CASCADE`
- `CONSTRAINT fk_rsh_user FOREIGN KEY(changed_by) REFERENCES users(id) ON DELETE CASCADE`
- `INDEX idx_rsh_request(request_id,created_at)`

**Application usage:** `post-requirement.php`, `request-details.php`, `request-service.php`

### `reviews`

| Column | Definition |
|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` |
| `request_id` | `BIGINT UNSIGNED NOT NULL UNIQUE` |
| `customer_id` | `BIGINT UNSIGNED NOT NULL` |
| `target_user_id` | `BIGINT UNSIGNED NOT NULL` |
| `rating` | `TINYINT UNSIGNED NOT NULL` |
| `comment` | `TEXT NULL` |
| `status` | `ENUM('published','hidden','removed') NOT NULL DEFAULT 'published'` |
| `created_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` |

**Keys / constraints declared at creation**

- `CONSTRAINT fk_review_request FOREIGN KEY(request_id) REFERENCES service_requests(id) ON DELETE CASCADE`
- `CONSTRAINT fk_review_customer FOREIGN KEY(customer_id) REFERENCES users(id) ON DELETE CASCADE`
- `CONSTRAINT fk_review_target FOREIGN KEY(target_user_id) REFERENCES users(id) ON DELETE CASCADE`
- `CONSTRAINT chk_rating CHECK(rating BETWEEN 1 AND 5)`
- `INDEX idx_reviews_target(target_user_id,status)`

**Post-create migration additions**

- `INDEX idx_reviews_customer_created(customer_id,created_at,id)`
- `INDEX idx_reviews_target_created(target_user_id,status,created_at,id)`

**Application usage:** `about.php`, `admin/_nav.php`, `admin/index.php`, `admin/reviews.php`, `business.php`, `includes/functions.php`, `includes/navbar.php`, `index.php`, `privacy.php`, `provider.php`, `request-details.php`, `reviews.php`, `search.php`, `terms.php`

### `favorites`

| Column | Definition |
|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` |
| `customer_id` | `BIGINT UNSIGNED NOT NULL` |
| `target_user_id` | `BIGINT UNSIGNED NOT NULL` |
| `created_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` |

**Keys / constraints declared at creation**

- `CONSTRAINT fk_fav_customer FOREIGN KEY(customer_id) REFERENCES users(id) ON DELETE CASCADE`
- `CONSTRAINT fk_fav_target FOREIGN KEY(target_user_id) REFERENCES users(id) ON DELETE CASCADE`
- `UNIQUE KEY uq_favorite(customer_id,target_user_id)`

**Post-create migration additions**

- `INDEX idx_favorites_customer_created(customer_id,created_at,id)`

**Application usage:** `ajax/favorite.php`, `favorites.php`, `includes/functions.php`, `includes/navbar.php`, `privacy.php`

### `notifications`

| Column | Definition |
|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` |
| `user_id` | `BIGINT UNSIGNED NOT NULL` |
| `type` | `VARCHAR(80) NOT NULL` |
| `title` | `VARCHAR(180) NOT NULL` |
| `message` | `VARCHAR(500) NOT NULL` |
| `link` | `VARCHAR(255) NULL` |
| `is_read` | `TINYINT(1) NOT NULL DEFAULT 0` |
| `created_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` |

**Keys / constraints declared at creation**

- `CONSTRAINT fk_notification_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE`
- `INDEX idx_notifications_user(user_id,is_read,created_at)`

**Application usage:** `includes/billing.php`, `includes/functions.php`, `includes/navbar.php`, `notifications.php`, `privacy.php`, `request-details.php`, `request-service.php`, `reviews.php`

### `reports`

| Column | Definition |
|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` |
| `reporter_id` | `BIGINT UNSIGNED NOT NULL` |
| `target_type` | `ENUM('provider','business','review') NOT NULL` |
| `target_id` | `BIGINT UNSIGNED NOT NULL` |
| `reason` | `ENUM('fake_profile','wrong_information','spam','fraud_concern','inappropriate_content','other') NOT NULL` |
| `details` | `TEXT NULL` |
| `status` | `ENUM('open','investigating','resolved','dismissed') NOT NULL DEFAULT 'open'` |
| `resolved_by` | `BIGINT UNSIGNED NULL` |
| `resolution_note` | `VARCHAR(500) NULL` |
| `created_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` |

**Keys / constraints declared at creation**

- `CONSTRAINT fk_reporter FOREIGN KEY(reporter_id) REFERENCES users(id) ON DELETE CASCADE`
- `CONSTRAINT fk_report_admin FOREIGN KEY(resolved_by) REFERENCES users(id) ON DELETE SET NULL`
- `INDEX idx_reports_status(status)`

**Post-create migration additions**

- `INDEX idx_reports_created(created_at,id)`

**Application usage:** `admin/_nav.php`, `admin/reports.php`, `report.php`

### `platform_activity`

| Column | Definition |
|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` |
| `actor_id` | `BIGINT UNSIGNED NULL` |
| `action` | `VARCHAR(100) NOT NULL` |
| `target_type` | `VARCHAR(60) NULL` |
| `target_id` | `BIGINT UNSIGNED NULL` |
| `details` | `VARCHAR(500) NULL` |
| `created_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` |

**Keys / constraints declared at creation**

- `CONSTRAINT fk_activity_actor FOREIGN KEY(actor_id) REFERENCES users(id) ON DELETE SET NULL`
- `INDEX idx_activity_created(created_at)`
- `INDEX idx_activity_action(action)`

**Post-create migration additions**

- `INDEX idx_activity_actor_created(actor_id,created_at)`

**Application usage:** `admin/index.php`, `includes/functions.php`

### `subscriptions`

| Column | Definition |
|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` |
| `user_id` | `BIGINT UNSIGNED NOT NULL` |
| `plan` | `ENUM('free','professional','business') NOT NULL DEFAULT 'free'` |
| `status` | `ENUM('active','scheduled','expired','cancelled','pending','suspended') NOT NULL DEFAULT 'active'` |
| `starts_at` | `DATETIME NULL` |
| `ends_at` | `DATETIME NULL` |
| `price` | `DECIMAL(10,2) NOT NULL DEFAULT 0` |
| `created_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` |
| `plan_id` | `INT UNSIGNED NULL AFTER plan` |
| `source_payment_id` | `BIGINT UNSIGNED NULL AFTER plan_id` |
| `billing_period_months` | `TINYINT UNSIGNED NOT NULL DEFAULT 1 AFTER source_payment_id` |
| `invoice_reference` | `VARCHAR(80) NULL AFTER price` |
| `suspension_reason` | `VARCHAR(255) NULL AFTER invoice_reference` |
| `benefits_applied_at` | `DATETIME NULL AFTER suspension_reason` |

**Keys / constraints declared at creation**

- `CONSTRAINT fk_subscription_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE`
- `INDEX idx_subscription_user(user_id,status)`

**Post-create migration additions**

- `UNIQUE KEY uq_subscription_source_payment(source_payment_id)`
- `INDEX idx_subscription_schedule(user_id,status,starts_at,ends_at)`
- `FOREIGN KEY fk_subscription_plan(plan_id) → subscription_plans(id) ON DELETE RESTRICT`
- `FOREIGN KEY fk_subscription_source_payment(source_payment_id) → payments(id) ON DELETE RESTRICT`

**Application usage:** `admin/_nav.php`, `admin/payment-methods.php`, `admin/subscriptions.php`, `billing/history.php`, `includes/billing.php`, `includes/functions.php`

### `payments`

| Column | Definition |
|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` |
| `user_id` | `BIGINT UNSIGNED NOT NULL` |
| `subscription_id` | `BIGINT UNSIGNED NULL` |
| `provider` | `VARCHAR(50) NULL` |
| `provider_payment_id` | `VARCHAR(190) NULL` |
| `amount` | `DECIMAL(10,2) NOT NULL` |
| `currency` | `CHAR(3) NOT NULL DEFAULT 'INR'` |
| `status` | `ENUM('pending','paid','failed','cancelled','refunded','partially_refunded','disputed','requires_review') NOT NULL DEFAULT 'pending'` |
| `created_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` |
| `payment_method_id` | `BIGINT UNSIGNED NULL AFTER subscription_id` |
| `payment_method_code_snapshot` | `VARCHAR(60) NULL AFTER payment_method_id` |
| `payment_method_name_snapshot` | `VARCHAR(120) NULL AFTER payment_method_code_snapshot` |
| `payment_method_type_snapshot` | `VARCHAR(40) NULL AFTER payment_method_name_snapshot` |
| `manual_instructions_snapshot` | `VARCHAR(2000) NULL AFTER payment_method_type_snapshot` |
| `merchant_upi_id_snapshot` | `VARCHAR(190) NULL AFTER manual_instructions_snapshot` |
| `bank_beneficiary_snapshot` | `VARCHAR(160) NULL AFTER merchant_upi_id_snapshot` |
| `bank_reference_snapshot` | `VARCHAR(190) NULL AFTER bank_beneficiary_snapshot` |
| `plan_id` | `INT UNSIGNED NULL AFTER subscription_id` |
| `plan_code_snapshot` | `VARCHAR(40) NULL AFTER plan_id` |
| `plan_name_snapshot` | `VARCHAR(80) NULL AFTER plan_code_snapshot` |
| `subtotal_amount` | `DECIMAL(10,2) NULL AFTER plan_name_snapshot` |
| `tax_amount` | `DECIMAL(10,2) NOT NULL DEFAULT 0 AFTER subtotal_amount` |
| `billing_period_months` | `TINYINT UNSIGNED NOT NULL DEFAULT 1 AFTER tax_amount` |
| `idempotency_key` | `CHAR(64) NULL AFTER billing_period_months` |
| `provider_order_id` | `VARCHAR(190) NULL AFTER provider` |
| `gateway_callback_verified_at` | `DATETIME NULL AFTER provider_payment_id` |
| `reconciliation_status` | `ENUM('pending','matched','warning','manual_review') NOT NULL DEFAULT 'pending' AFTER status` |
| `reconciliation_note` | `VARCHAR(500) NULL AFTER reconciliation_status` |
| `paid_at` | `DATETIME NULL AFTER reconciliation_note` |
| `failed_at` | `DATETIME NULL AFTER paid_at` |
| `cancelled_at` | `DATETIME NULL AFTER failed_at` |
| `refunded_at` | `DATETIME NULL AFTER cancelled_at` |
| `disputed_at` | `DATETIME NULL AFTER refunded_at` |
| `invoice_reference` | `VARCHAR(80) NULL AFTER disputed_at` |
| `checkout_expires_at` | `DATETIME NULL AFTER invoice_reference` |

**Keys / constraints declared at creation**

- `CONSTRAINT fk_payment_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE`
- `CONSTRAINT fk_payment_sub FOREIGN KEY(subscription_id) REFERENCES subscriptions(id) ON DELETE SET NULL`
- `INDEX idx_payment_status(status,created_at)`

**Post-create migration additions**

- `UNIQUE KEY uq_payment_idempotency(idempotency_key)`
- `UNIQUE KEY uq_payment_provider_order(provider,provider_order_id)`
- `UNIQUE KEY uq_payment_provider_payment(provider,provider_payment_id)`
- `INDEX idx_payment_reconcile(reconciliation_status,status,created_at)`
- `FOREIGN KEY fk_payment_plan(plan_id) → subscription_plans(id) ON DELETE RESTRICT`
- `FOREIGN KEY fk_payment_method(payment_method_id) → payment_methods(id) ON DELETE SET NULL`
- `INDEX idx_payment_method(payment_method_id,status,created_at)`

**Application usage:** `admin/_nav.php`, `admin/index.php`, `admin/payment-detail.php`, `admin/payments.php`, `billing/history.php`, `includes/billing.php`, `terms.php`

### `advertisements`

| Column | Definition |
|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` |
| `title` | `VARCHAR(180) NOT NULL` |
| `description` | `VARCHAR(500) NULL` |
| `image` | `VARCHAR(255) NULL` |
| `target_url` | `VARCHAR(255) NULL` |
| `placement` | `VARCHAR(80) NULL` |
| `budget` | `DECIMAL(10,2) NOT NULL DEFAULT 0` |
| `impressions` | `INT UNSIGNED NOT NULL DEFAULT 0` |
| `clicks` | `INT UNSIGNED NOT NULL DEFAULT 0` |
| `status` | `ENUM('draft','active','paused','expired') NOT NULL DEFAULT 'draft'` |
| `starts_at` | `DATETIME NULL` |
| `ends_at` | `DATETIME NULL` |
| `created_by` | `BIGINT UNSIGNED NOT NULL` |
| `sponsor_user_id` | `BIGINT UNSIGNED NULL` |
| `created_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` |

**Keys / constraints declared at creation**

- `CONSTRAINT fk_ad_admin FOREIGN KEY(created_by) REFERENCES users(id) ON DELETE RESTRICT`
- `CONSTRAINT fk_ad_sponsor FOREIGN KEY(sponsor_user_id) REFERENCES users(id) ON DELETE SET NULL`
- `INDEX idx_ads_status(status,starts_at,ends_at)`

**Application usage:** `admin/_nav.php`, `admin/advertisements.php`

### `subscription_plans`

| Column | Definition |
|---|---|
| `id` | `INT UNSIGNED AUTO_INCREMENT PRIMARY KEY` |
| `code` | `VARCHAR(40) NOT NULL UNIQUE` |
| `name` | `VARCHAR(80) NOT NULL` |
| `audience` | `ENUM('provider','business','both') NOT NULL DEFAULT 'both'` |
| `price_monthly` | `DECIMAL(10,2) NOT NULL DEFAULT 0` |
| `featured_days` | `INT UNSIGNED NOT NULL DEFAULT 0` |
| `lead_limit` | `INT UNSIGNED NULL` |
| `description` | `VARCHAR(255) NULL` |
| `is_active` | `TINYINT(1) NOT NULL DEFAULT 1` |
| `created_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` |
| `billing_period_months` | `TINYINT UNSIGNED NOT NULL DEFAULT 1 AFTER price_monthly` |
| `tax_rate_bps` | `SMALLINT UNSIGNED NOT NULL DEFAULT 0 AFTER billing_period_months` |
| `tax_label` | `VARCHAR(40) NOT NULL DEFAULT 'Tax' AFTER tax_rate_bps` |

**Application usage:** `admin/subscriptions.php`, `business/subscription.php`, `includes/billing.php`, `includes/functions.php`, `provider/subscription.php`

### `featured_listings`

| Column | Definition |
|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` |
| `user_id` | `BIGINT UNSIGNED NOT NULL` |
| `subscription_id` | `BIGINT UNSIGNED NULL` |
| `status` | `ENUM('pending','active','expired','cancelled') NOT NULL DEFAULT 'pending'` |
| `starts_at` | `DATETIME NULL` |
| `ends_at` | `DATETIME NULL` |
| `created_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` |

**Keys / constraints declared at creation**

- `CONSTRAINT fk_featured_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE`
- `CONSTRAINT fk_featured_sub FOREIGN KEY(subscription_id) REFERENCES subscriptions(id) ON DELETE SET NULL`
- `INDEX idx_featured(status,starts_at,ends_at)`

**Application usage:** `includes/billing.php`, `includes/functions.php`

### `lead_wallets`

| Column | Definition |
|---|---|
| `user_id` | `BIGINT UNSIGNED PRIMARY KEY` |
| `credits` | `INT UNSIGNED NOT NULL DEFAULT 0` |
| `updated_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` |

**Keys / constraints declared at creation**

- `CONSTRAINT fk_lead_wallet_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE`

**Application usage:** `includes/billing.php`, `includes/functions.php`

### `schema_migrations`

| Column | Definition |
|---|---|
| `version` | `VARCHAR(80) PRIMARY KEY` |
| `applied_at` | `TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP` |
| `checksum_sha256` | `CHAR(64) NULL` |

**Application usage:** No direct production-PHP reference found.

### `auth_tokens`

| Column | Definition |
|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` |
| `user_id` | `BIGINT UNSIGNED NOT NULL` |
| `purpose` | `ENUM('password_reset','email_verify') NOT NULL` |
| `selector` | `CHAR(16) NOT NULL` |
| `token_hash` | `CHAR(64) NOT NULL` |
| `expires_at` | `DATETIME NOT NULL` |
| `used_at` | `DATETIME NULL` |
| `requested_ip_hash` | `CHAR(64) NULL` |
| `created_at` | `TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP` |

**Keys / constraints declared at creation**

- `UNIQUE KEY uq_auth_token_selector(selector)`
- `INDEX idx_auth_token_user(user_id,purpose,used_at,expires_at)`
- `CONSTRAINT fk_auth_token_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE`

**Post-create migration additions**

- `INDEX idx_auth_token_expiry(purpose,used_at,expires_at)`

**Application usage:** `auth/reset-password.php`, `auth/verify-email.php`, `includes/functions.php`

### `auth_rate_limits`

| Column | Definition |
|---|---|
| `bucket_hash` | `CHAR(64) PRIMARY KEY` |
| `attempts` | `INT UNSIGNED NOT NULL DEFAULT 0` |
| `window_started_at` | `DATETIME NOT NULL` |
| `blocked_until` | `DATETIME NULL` |
| `updated_at` | `TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` |

**Keys / constraints declared at creation**

- `INDEX idx_auth_rate_blocked(blocked_until)`

**Application usage:** `includes/auth.php`

### `admin_mfa`

| Column | Definition |
|---|---|
| `user_id` | `BIGINT UNSIGNED PRIMARY KEY` |
| `secret_ciphertext` | `TEXT NOT NULL` |
| `secret_nonce` | `VARCHAR(128) NOT NULL` |
| `encryption_alg` | `VARCHAR(40) NOT NULL` |
| `enabled_at` | `DATETIME NOT NULL` |
| `last_used_step` | `BIGINT NULL` |
| `last_verified_at` | `DATETIME NULL` |
| `created_at` | `TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` |

**Keys / constraints declared at creation**

- `CONSTRAINT fk_admin_mfa_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE`

**Application usage:** `admin/mfa.php`, `includes/auth.php`

### `payment_methods`

| Column | Definition |
|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` |
| `code` | `VARCHAR(60) NOT NULL UNIQUE` |
| `name` | `VARCHAR(120) NOT NULL` |
| `method_type` | `ENUM('gateway','upi','bank_transfer') NOT NULL` |
| `gateway_code` | `VARCHAR(60) NULL` |
| `audience` | `ENUM('provider','business','both') NOT NULL DEFAULT 'both'` |
| `currency` | `CHAR(3) NOT NULL DEFAULT 'INR'` |
| `merchant_upi_id` | `VARCHAR(190) NULL` |
| `bank_beneficiary` | `VARCHAR(160) NULL` |
| `bank_reference` | `VARCHAR(190) NULL` |
| `display_instructions` | `VARCHAR(2000) NULL` |
| `display_order` | `INT UNSIGNED NOT NULL DEFAULT 100` |
| `is_active` | `TINYINT(1) NOT NULL DEFAULT 0` |
| `created_by` | `BIGINT UNSIGNED NOT NULL` |
| `updated_by` | `BIGINT UNSIGNED NOT NULL` |
| `created_at` | `TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` |

**Keys / constraints declared at creation**

- `CONSTRAINT fk_payment_method_created_by FOREIGN KEY(created_by) REFERENCES users(id) ON DELETE RESTRICT`
- `CONSTRAINT fk_payment_method_updated_by FOREIGN KEY(updated_by) REFERENCES users(id) ON DELETE RESTRICT`
- `INDEX idx_payment_method_active(audience,currency,is_active,display_order)`
- `INDEX idx_payment_method_type(method_type,gateway_code)`

**Application usage:** `admin/payment-detail.php`, `admin/payment-method-edit.php`, `admin/payment-methods.php`, `admin/payments.php`, `includes/billing.php`, `includes/functions.php`

### `payment_method_audit`

| Column | Definition |
|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` |
| `payment_method_id` | `BIGINT UNSIGNED NOT NULL` |
| `admin_user_id` | `BIGINT UNSIGNED NOT NULL` |
| `action` | `VARCHAR(40) NOT NULL` |
| `before_json` | `JSON NULL` |
| `after_json` | `JSON NULL` |
| `created_at` | `TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP` |

**Keys / constraints declared at creation**

- `CONSTRAINT fk_pma_method FOREIGN KEY(payment_method_id) REFERENCES payment_methods(id) ON DELETE RESTRICT`
- `CONSTRAINT fk_pma_admin FOREIGN KEY(admin_user_id) REFERENCES users(id) ON DELETE RESTRICT`
- `INDEX idx_pma_method(payment_method_id,created_at)`
- `INDEX idx_pma_admin(admin_user_id,created_at)`

**Application usage:** `admin/payment-methods.php`, `includes/functions.php`

### `checkout_intents`

| Column | Definition |
|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` |
| `token_hash` | `CHAR(64) NOT NULL` |
| `user_id` | `BIGINT UNSIGNED NOT NULL` |
| `user_role` | `ENUM('provider','business') NOT NULL` |
| `plan_id` | `INT UNSIGNED NOT NULL` |
| `plan_code_snapshot` | `VARCHAR(40) NOT NULL` |
| `plan_name_snapshot` | `VARCHAR(80) NOT NULL` |
| `currency` | `CHAR(3) NOT NULL DEFAULT 'INR'` |
| `subtotal_amount` | `DECIMAL(10,2) NOT NULL` |
| `tax_amount` | `DECIMAL(10,2) NOT NULL DEFAULT 0` |
| `total_amount` | `DECIMAL(10,2) NOT NULL` |
| `billing_period_months` | `TINYINT UNSIGNED NOT NULL DEFAULT 1` |
| `status` | `ENUM('selecting_method','pending_gateway','pending_manual','paid','failed','cancelled','expired') NOT NULL DEFAULT 'selecting_method'` |
| `payment_id` | `BIGINT UNSIGNED NULL` |
| `expires_at` | `DATETIME NOT NULL` |
| `created_at` | `TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` |

**Keys / constraints declared at creation**

- `UNIQUE KEY uq_checkout_token(token_hash)`
- `INDEX idx_checkout_user(user_id,status,expires_at)`
- `INDEX idx_checkout_plan(plan_id,status)`
- `CONSTRAINT fk_checkout_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE`
- `CONSTRAINT fk_checkout_plan FOREIGN KEY(plan_id) REFERENCES subscription_plans(id) ON DELETE RESTRICT`
- `CONSTRAINT fk_checkout_payment FOREIGN KEY(payment_id) REFERENCES payments(id) ON DELETE SET NULL`

**Post-create migration additions**

- `INDEX idx_checkout_expiry(status,expires_at)`

**Application usage:** `includes/billing.php`

### `payment_status_history`

| Column | Definition |
|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` |
| `payment_id` | `BIGINT UNSIGNED NOT NULL` |
| `old_status` | `VARCHAR(40) NULL` |
| `new_status` | `VARCHAR(40) NOT NULL` |
| `source` | `ENUM('checkout','callback','webhook','reconciliation','admin','system') NOT NULL` |
| `external_event_key` | `VARCHAR(190) NULL` |
| `note` | `VARCHAR(500) NULL` |
| `actor_user_id` | `BIGINT UNSIGNED NULL` |
| `created_at` | `TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP` |

**Keys / constraints declared at creation**

- `CONSTRAINT fk_psh_payment FOREIGN KEY(payment_id) REFERENCES payments(id) ON DELETE CASCADE`
- `CONSTRAINT fk_psh_actor FOREIGN KEY(actor_user_id) REFERENCES users(id) ON DELETE SET NULL`
- `INDEX idx_psh_payment(payment_id,created_at)`
- `INDEX idx_psh_external(external_event_key)`

**Application usage:** `admin/payment-detail.php`, `includes/billing.php`

### `payment_webhook_events`

| Column | Definition |
|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` |
| `provider` | `VARCHAR(40) NOT NULL` |
| `event_key` | `VARCHAR(190) NOT NULL` |
| `event_type` | `VARCHAR(120) NOT NULL` |
| `payload_sha256` | `CHAR(64) NOT NULL` |
| `provider_payment_id` | `VARCHAR(190) NULL` |
| `provider_order_id` | `VARCHAR(190) NULL` |
| `signature_valid` | `TINYINT(1) NOT NULL DEFAULT 0` |
| `processing_status` | `ENUM('received','processed','ignored','failed') NOT NULL DEFAULT 'received'` |
| `processing_note` | `VARCHAR(500) NULL` |
| `received_at` | `TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP` |
| `processed_at` | `DATETIME NULL` |

**Keys / constraints declared at creation**

- `UNIQUE KEY uq_webhook_event(provider,event_key)`
- `INDEX idx_webhook_payment(provider_payment_id)`
- `INDEX idx_webhook_order(provider_order_id)`
- `INDEX idx_webhook_status(processing_status,received_at)`

**Application usage:** `admin/payment-detail.php`, `includes/billing.php`

### `manual_payment_submissions`

| Column | Definition |
|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` |
| `payment_id` | `BIGINT UNSIGNED NOT NULL` |
| `user_id` | `BIGINT UNSIGNED NOT NULL` |
| `payer_reference` | `VARCHAR(190) NOT NULL` |
| `payer_note` | `VARCHAR(500) NULL` |
| `status` | `ENUM('pending','verified','rejected') NOT NULL DEFAULT 'pending'` |
| `reviewed_by` | `BIGINT UNSIGNED NULL` |
| `review_note` | `VARCHAR(500) NULL` |
| `submitted_at` | `TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP` |
| `reviewed_at` | `DATETIME NULL` |

**Keys / constraints declared at creation**

- `UNIQUE KEY uq_manual_payment(payment_id)`
- `INDEX idx_manual_status(status,submitted_at)`
- `CONSTRAINT fk_manual_payment FOREIGN KEY(payment_id) REFERENCES payments(id) ON DELETE CASCADE`
- `CONSTRAINT fk_manual_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE`
- `CONSTRAINT fk_manual_reviewer FOREIGN KEY(reviewed_by) REFERENCES users(id) ON DELETE SET NULL`

**Application usage:** `admin/payment-detail.php`, `includes/billing.php`

### `payment_reconciliation_jobs`

| Column | Definition |
|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` |
| `webhook_event_id` | `BIGINT UNSIGNED NULL` |
| `payment_id` | `BIGINT UNSIGNED NULL` |
| `status` | `ENUM('queued','processing','retry','done','dead') NOT NULL DEFAULT 'queued'` |
| `attempts` | `TINYINT UNSIGNED NOT NULL DEFAULT 0` |
| `max_attempts` | `TINYINT UNSIGNED NOT NULL DEFAULT 5` |
| `next_attempt_at` | `DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP` |
| `locked_at` | `DATETIME NULL` |
| `last_error` | `VARCHAR(500) NULL` |
| `created_at` | `TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` |

**Keys / constraints declared at creation**

- `UNIQUE KEY uq_reconcile_webhook_event(webhook_event_id)`
- `INDEX idx_reconcile_due(status,next_attempt_at,id)`
- `INDEX idx_reconcile_payment(payment_id,status)`
- `CONSTRAINT fk_reconcile_webhook FOREIGN KEY(webhook_event_id) REFERENCES payment_webhook_events(id) ON DELETE CASCADE`
- `CONSTRAINT fk_reconcile_payment FOREIGN KEY(payment_id) REFERENCES payments(id) ON DELETE CASCADE`

**Post-create migration additions**

- `INDEX idx_reconcile_payment_due(payment_id,status,next_attempt_at)`

**Application usage:** `includes/billing.php`

## Important enumerated business states

- User roles: `customer`, `provider`, `business`, `admin`.
- User status: `active`, `blocked`, `pending`.
- Provider/business verification: `pending`, `verified`, `rejected`.
- Request status: `pending`, `accepted`, `rejected`, `in_progress`, `completed`, `cancelled`.
- Review status: `published`, `hidden`, `removed`.
- Report status: `open`, `investigating`, `resolved`, `dismissed`.
- Advertisement status: `draft`, `active`, `paused`, `expired`.
- Payment lifecycle: `pending`, `paid`, `failed`, `cancelled`, `refunded`, `partially_refunded`, `disputed`, `requires_review`.
- Subscription lifecycle: `active`, `scheduled`, `expired`, `cancelled`, `pending`, `suspended`.
- Checkout intent: `selecting_method`, `pending_gateway`, `pending_manual`, `paid`, `failed`, `cancelled`, `expired`.
- Manual payment: `pending`, `verified`, `rejected`; reconciliation jobs: `queued`, `processing`, `retry`, `done`, `dead`.

## Migration SQL inventory

- `database/localconnect_db.sql`
- `database/phase2_migration.sql`
- `database/phase3_migration.sql`
- `database/phase4_migration.sql`
- `database/phase5_migration.sql`
- `database/phase6_migration.sql`
- `database/phase7_migration.sql`
- `database/production/20260924_001_security_foundation.sql`
- `database/production/20260924_001_security_foundation_preflight.sql`
- `database/production/20260924_001_security_foundation_rollback.sql`
- `database/production/20260924_002_payment_methods.sql`
- `database/production/20260924_002_payment_methods_preflight.sql`
- `database/production/20260924_002_payment_methods_rollback.sql`
- `database/production/20260924_003_checkout_webhooks.sql`
- `database/production/20260924_003_checkout_webhooks_preflight.sql`
- `database/production/20260924_003_checkout_webhooks_rollback.sql`
- `database/production/20260924_004_performance_reliability.sql`
- `database/production/20260924_004_preflight.sql`
- `database/production/20260924_004_rollback.sql`
- `database/production/20260924_005_production_hardening.sql`
- `database/production/20260924_005_production_hardening_preflight.sql`
- `database/production/20260924_005_production_hardening_rollback.sql`
- `database/production/fresh_schema.sql`
- `database/production/least_privilege_grants.template.sql`

## Critical database parity rules for later phases

- Preserve all existing table/column names unless a compatibility migration explicitly proves otherwise.
- Preserve foreign-key delete behavior, unique constraints, indexes, defaults and enum/status values.
- Preserve transaction boundaries in registration, request creation/status changes, payment reconciliation and entitlement activation.
- Do not mark payment paid or grant entitlement from browser data alone; server reconciliation/manual admin verification is authoritative.
- Existing production data must be upgraded with idempotent/non-destructive migrations; never run `fresh_schema.sql` against a populated production DB as an automatic startup action.
