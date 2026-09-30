-- Fresh EMPTY database bootstrap only. Run against a pre-created database.
-- Contains no demo users/passwords and no DROP statements.

CREATE TABLE users (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(120) NOT NULL,
 email VARCHAR(190) NOT NULL UNIQUE,
 phone VARCHAR(25) NULL,
 password_hash VARCHAR(255) NOT NULL,
 role ENUM('customer','provider','business','admin') NOT NULL DEFAULT 'customer',
 status ENUM('active','blocked','pending') NOT NULL DEFAULT 'active',
 profile_image VARCHAR(255) NULL,
 city VARCHAR(100) NULL,
 state VARCHAR(100) NULL,
 area VARCHAR(150) NULL,
 pincode VARCHAR(12) NULL,
 latitude DECIMAL(10,7) NULL,
 longitude DECIMAL(10,7) NULL,
 last_login_at DATETIME NULL,
 email_verified_at DATETIME NULL,
 session_version INT UNSIGNED NOT NULL DEFAULT 1,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 INDEX idx_users_role_status(role,status), INDEX idx_users_location(city,state,area), INDEX idx_users_name(name)
) ENGINE=InnoDB;

CREATE TABLE locations (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,user_id BIGINT UNSIGNED NOT NULL,label VARCHAR(80) DEFAULT 'Primary',address_line VARCHAR(255) NULL,area VARCHAR(150) NULL,city VARCHAR(100) NOT NULL,state VARCHAR(100) NOT NULL,pincode VARCHAR(12) NULL,latitude DECIMAL(10,7) NULL,longitude DECIMAL(10,7) NULL,is_default TINYINT(1) NOT NULL DEFAULT 0,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 CONSTRAINT fk_locations_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE, INDEX idx_locations_city(city,state,area)
) ENGINE=InnoDB;

CREATE TABLE categories (
 id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,name VARCHAR(120) NOT NULL UNIQUE,slug VARCHAR(140) NOT NULL UNIQUE,icon VARCHAR(80) NULL,description VARCHAR(255) NULL,is_active TINYINT(1) NOT NULL DEFAULT 1,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, INDEX idx_categories_active(is_active)
) ENGINE=InnoDB;

CREATE TABLE provider_profiles (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,user_id BIGINT UNSIGNED NOT NULL UNIQUE,headline VARCHAR(180) NULL,about TEXT NULL,experience_years SMALLINT UNSIGNED DEFAULT 0,service_area VARCHAR(255) NULL,price_min DECIMAL(10,2) NULL,price_max DECIMAL(10,2) NULL,availability_status ENUM('available','busy','unavailable') NOT NULL DEFAULT 'available',working_hours VARCHAR(255) NULL,verification_status ENUM('pending','verified','rejected') NOT NULL DEFAULT 'pending',verified_at DATETIME NULL,is_featured TINYINT(1) NOT NULL DEFAULT 0,profile_views INT UNSIGNED NOT NULL DEFAULT 0,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 CONSTRAINT fk_provider_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE, INDEX idx_provider_verify(verification_status),INDEX idx_provider_available(availability_status)
) ENGINE=InnoDB;

CREATE TABLE business_profiles (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,user_id BIGINT UNSIGNED NOT NULL UNIQUE,category_id INT UNSIGNED NULL,business_name VARCHAR(180) NULL,slug VARCHAR(200) NULL UNIQUE,logo VARCHAR(255) NULL,description TEXT NULL,address VARCHAR(255) NULL,phone VARCHAR(25) NULL,opening_time TIME NULL,closing_time TIME NULL,price_min DECIMAL(10,2) NULL,price_max DECIMAL(10,2) NULL,website VARCHAR(255) NULL,social_links JSON NULL,verification_status ENUM('pending','verified','rejected') NOT NULL DEFAULT 'pending',verified_at DATETIME NULL,is_featured TINYINT(1) NOT NULL DEFAULT 0,profile_views INT UNSIGNED NOT NULL DEFAULT 0,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 CONSTRAINT fk_business_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,CONSTRAINT fk_business_category FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE SET NULL,INDEX idx_business_name(business_name),INDEX idx_business_verify(verification_status)
) ENGINE=InnoDB;

CREATE TABLE services (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,category_id INT UNSIGNED NOT NULL,name VARCHAR(160) NOT NULL,slug VARCHAR(180) NOT NULL,description TEXT NULL,is_active TINYINT(1) NOT NULL DEFAULT 1,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 CONSTRAINT fk_services_category FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE RESTRICT, UNIQUE KEY uq_service_category_slug(category_id,slug),INDEX idx_service_name(name)
) ENGINE=InnoDB;

CREATE TABLE provider_services (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,provider_user_id BIGINT UNSIGNED NOT NULL,service_id BIGINT UNSIGNED NOT NULL,title VARCHAR(180) NULL,description TEXT NULL,price_from DECIMAL(10,2) NULL,price_to DECIMAL(10,2) NULL,is_active TINYINT(1) NOT NULL DEFAULT 1,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 CONSTRAINT fk_ps_user FOREIGN KEY(provider_user_id) REFERENCES users(id) ON DELETE CASCADE,CONSTRAINT fk_ps_service FOREIGN KEY(service_id) REFERENCES services(id) ON DELETE CASCADE,UNIQUE KEY uq_provider_service(provider_user_id,service_id),INDEX idx_ps_active(is_active)
) ENGINE=InnoDB;

CREATE TABLE portfolio_images (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,user_id BIGINT UNSIGNED NOT NULL,image_path VARCHAR(255) NOT NULL,caption VARCHAR(255) NULL,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 CONSTRAINT fk_portfolio_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,INDEX idx_portfolio_user(user_id,created_at)
) ENGINE=InnoDB;

CREATE TABLE service_requests (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,customer_id BIGINT UNSIGNED NOT NULL,provider_id BIGINT UNSIGNED NULL,business_id BIGINT UNSIGNED NULL,category_id INT UNSIGNED NOT NULL,service_id BIGINT UNSIGNED NULL,request_type ENUM('direct','requirement') NOT NULL DEFAULT 'direct',title VARCHAR(180) NOT NULL,description TEXT NOT NULL,location_text VARCHAR(255) NOT NULL,preferred_date DATE NULL,preferred_time TIME NULL,budget_min DECIMAL(10,2) NULL,budget_max DECIMAL(10,2) NULL,additional_notes TEXT NULL,status ENUM('pending','accepted','rejected','in_progress','completed','cancelled') NOT NULL DEFAULT 'pending',created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 CONSTRAINT fk_sr_customer FOREIGN KEY(customer_id) REFERENCES users(id) ON DELETE CASCADE,CONSTRAINT fk_sr_provider FOREIGN KEY(provider_id) REFERENCES users(id) ON DELETE SET NULL,CONSTRAINT fk_sr_business FOREIGN KEY(business_id) REFERENCES users(id) ON DELETE SET NULL,CONSTRAINT fk_sr_category FOREIGN KEY(category_id) REFERENCES categories(id),CONSTRAINT fk_sr_service FOREIGN KEY(service_id) REFERENCES services(id) ON DELETE SET NULL,INDEX idx_sr_status(status),INDEX idx_sr_provider(provider_id,status),INDEX idx_sr_customer(customer_id,status),INDEX idx_sr_category(category_id,status),INDEX idx_sr_type_status_service(request_type,status,service_id),INDEX idx_sr_business(business_id,status)
) ENGINE=InnoDB;

CREATE TABLE request_status_history (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,request_id BIGINT UNSIGNED NOT NULL,status ENUM('pending','accepted','rejected','in_progress','completed','cancelled') NOT NULL,changed_by BIGINT UNSIGNED NOT NULL,note VARCHAR(500) NULL,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT fk_rsh_request FOREIGN KEY(request_id) REFERENCES service_requests(id) ON DELETE CASCADE,CONSTRAINT fk_rsh_user FOREIGN KEY(changed_by) REFERENCES users(id) ON DELETE CASCADE,INDEX idx_rsh_request(request_id,created_at)
) ENGINE=InnoDB;

CREATE TABLE reviews (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,request_id BIGINT UNSIGNED NOT NULL UNIQUE,customer_id BIGINT UNSIGNED NOT NULL,target_user_id BIGINT UNSIGNED NOT NULL,rating TINYINT UNSIGNED NOT NULL,comment TEXT NULL,status ENUM('published','hidden','removed') NOT NULL DEFAULT 'published',created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 CONSTRAINT fk_review_request FOREIGN KEY(request_id) REFERENCES service_requests(id) ON DELETE CASCADE,CONSTRAINT fk_review_customer FOREIGN KEY(customer_id) REFERENCES users(id) ON DELETE CASCADE,CONSTRAINT fk_review_target FOREIGN KEY(target_user_id) REFERENCES users(id) ON DELETE CASCADE,CONSTRAINT chk_rating CHECK(rating BETWEEN 1 AND 5),INDEX idx_reviews_target(target_user_id,status)
) ENGINE=InnoDB;

CREATE TABLE favorites (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,customer_id BIGINT UNSIGNED NOT NULL,target_user_id BIGINT UNSIGNED NOT NULL,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,CONSTRAINT fk_fav_customer FOREIGN KEY(customer_id) REFERENCES users(id) ON DELETE CASCADE,CONSTRAINT fk_fav_target FOREIGN KEY(target_user_id) REFERENCES users(id) ON DELETE CASCADE,UNIQUE KEY uq_favorite(customer_id,target_user_id)
) ENGINE=InnoDB;

CREATE TABLE notifications (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,user_id BIGINT UNSIGNED NOT NULL,type VARCHAR(80) NOT NULL,title VARCHAR(180) NOT NULL,message VARCHAR(500) NOT NULL,link VARCHAR(255) NULL,is_read TINYINT(1) NOT NULL DEFAULT 0,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,CONSTRAINT fk_notification_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,INDEX idx_notifications_user(user_id,is_read,created_at)
) ENGINE=InnoDB;

CREATE TABLE reports (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,reporter_id BIGINT UNSIGNED NOT NULL,target_type ENUM('provider','business','review') NOT NULL,target_id BIGINT UNSIGNED NOT NULL,reason ENUM('fake_profile','wrong_information','spam','fraud_concern','inappropriate_content','other') NOT NULL,details TEXT NULL,status ENUM('open','investigating','resolved','dismissed') NOT NULL DEFAULT 'open',resolved_by BIGINT UNSIGNED NULL,resolution_note VARCHAR(500) NULL,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,CONSTRAINT fk_reporter FOREIGN KEY(reporter_id) REFERENCES users(id) ON DELETE CASCADE,CONSTRAINT fk_report_admin FOREIGN KEY(resolved_by) REFERENCES users(id) ON DELETE SET NULL,INDEX idx_reports_status(status)
) ENGINE=InnoDB;

CREATE TABLE platform_activity (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,actor_id BIGINT UNSIGNED NULL,action VARCHAR(100) NOT NULL,target_type VARCHAR(60) NULL,target_id BIGINT UNSIGNED NULL,details VARCHAR(500) NULL,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,CONSTRAINT fk_activity_actor FOREIGN KEY(actor_id) REFERENCES users(id) ON DELETE SET NULL,INDEX idx_activity_created(created_at),INDEX idx_activity_action(action)
) ENGINE=InnoDB;

CREATE TABLE subscriptions (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,user_id BIGINT UNSIGNED NOT NULL,plan ENUM('free','professional','business') NOT NULL DEFAULT 'free',status ENUM('active','expired','cancelled','pending') NOT NULL DEFAULT 'active',starts_at DATETIME NULL,ends_at DATETIME NULL,price DECIMAL(10,2) NOT NULL DEFAULT 0,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,CONSTRAINT fk_subscription_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,INDEX idx_subscription_user(user_id,status)
) ENGINE=InnoDB;

CREATE TABLE payments (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,user_id BIGINT UNSIGNED NOT NULL,subscription_id BIGINT UNSIGNED NULL,provider VARCHAR(50) NULL,provider_payment_id VARCHAR(190) NULL,amount DECIMAL(10,2) NOT NULL,currency CHAR(3) NOT NULL DEFAULT 'INR',status ENUM('pending','paid','failed','refunded') NOT NULL DEFAULT 'pending',created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,CONSTRAINT fk_payment_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,CONSTRAINT fk_payment_sub FOREIGN KEY(subscription_id) REFERENCES subscriptions(id) ON DELETE SET NULL,INDEX idx_payment_status(status,created_at)
) ENGINE=InnoDB;

CREATE TABLE advertisements (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,title VARCHAR(180) NOT NULL,description VARCHAR(500) NULL,image VARCHAR(255) NULL,target_url VARCHAR(255) NULL,placement VARCHAR(80) NULL,budget DECIMAL(10,2) NOT NULL DEFAULT 0,impressions INT UNSIGNED NOT NULL DEFAULT 0,clicks INT UNSIGNED NOT NULL DEFAULT 0,status ENUM('draft','active','paused','expired') NOT NULL DEFAULT 'draft',starts_at DATETIME NULL,ends_at DATETIME NULL,created_by BIGINT UNSIGNED NOT NULL,sponsor_user_id BIGINT UNSIGNED NULL,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,CONSTRAINT fk_ad_admin FOREIGN KEY(created_by) REFERENCES users(id) ON DELETE RESTRICT,CONSTRAINT fk_ad_sponsor FOREIGN KEY(sponsor_user_id) REFERENCES users(id) ON DELETE SET NULL,INDEX idx_ads_status(status,starts_at,ends_at)
) ENGINE=InnoDB;

INSERT INTO categories(name,slug,icon) VALUES
('Home Services','home-services','fa-house'),('Electrical','electrical','fa-bolt'),('Plumbing','plumbing','fa-faucet-drip'),('Carpenter','carpenter','fa-hammer'),('Painting','painting','fa-paint-roller'),('Cleaning','cleaning','fa-broom'),('Appliance Repair','appliance-repair','fa-screwdriver-wrench'),('AC & Cooling','ac-cooling','fa-snowflake'),('Computer & Mobile Repair','computer-mobile-repair','fa-laptop'),('Automotive','automotive','fa-car'),('Beauty & Salon','beauty-salon','fa-scissors'),('Education & Tutors','education-tutors','fa-graduation-cap'),('Photography','photography','fa-camera'),('Events','events','fa-calendar-days'),('Construction','construction','fa-helmet-safety'),('Tailoring','tailoring','fa-shirt'),('Fitness','fitness','fa-dumbbell'),('Other Services','other-services','fa-ellipsis');

-- Phase 2 demo service catalogue
INSERT INTO services(category_id,name,slug,description) VALUES
(2,'Electrician','electrician','General electrical installation and repair'),
(2,'Switchboard Repair','switchboard-repair','Switchboard inspection and repair'),
(3,'Plumber','plumber','General plumbing work'),
(3,'Leak Repair','leak-repair','Pipe and tap leak repair'),
(4,'Carpentry Work','carpentry-work','General carpentry and furniture repair'),
(6,'Home Cleaning','home-cleaning','Residential cleaning service'),
(7,'Washing Machine Repair','washing-machine-repair','Washing machine diagnostics and repair'),
(8,'AC Repair','ac-repair','Air conditioner diagnostics and repair'),
(8,'AC Installation','ac-installation','Air conditioner installation'),
(9,'Computer Repair','computer-repair','Desktop and laptop repair'),
(9,'Mobile Repair','mobile-repair','Mobile phone diagnostics and repair'),
(10,'Car Mechanic','car-mechanic','General car repair and maintenance'),
(11,'Salon Services','salon-services','Beauty and salon services'),
(12,'Home Tutor','home-tutor','Private tutoring services'),
(13,'Event Photography','event-photography','Photography for local events'),
(15,'Masonry Work','masonry-work','Construction and masonry work'),
(16,'Tailoring & Alteration','tailoring-alteration','Clothing tailoring and alterations'),
(17,'Personal Fitness Training','personal-fitness-training','Personal fitness coaching');
CREATE TABLE IF NOT EXISTS subscription_plans (
 id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, code VARCHAR(40) NOT NULL UNIQUE, name VARCHAR(80) NOT NULL, audience ENUM('provider','business','both') NOT NULL DEFAULT 'both', price_monthly DECIMAL(10,2) NOT NULL DEFAULT 0, featured_days INT UNSIGNED NOT NULL DEFAULT 0, lead_limit INT UNSIGNED NULL, description VARCHAR(255) NULL, is_active TINYINT(1) NOT NULL DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;
INSERT IGNORE INTO subscription_plans(code,name,audience,price_monthly,featured_days,lead_limit,description) VALUES
('free','Free','both',0,0,5,'Basic local listing'),('professional','Professional','provider',499,7,50,'For independent professionals'),('business','Business','business',999,15,NULL,'For local businesses');
CREATE TABLE IF NOT EXISTS featured_listings (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,user_id BIGINT UNSIGNED NOT NULL,subscription_id BIGINT UNSIGNED NULL,status ENUM('pending','active','expired','cancelled') NOT NULL DEFAULT 'pending',starts_at DATETIME NULL,ends_at DATETIME NULL,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,CONSTRAINT fk_featured_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,CONSTRAINT fk_featured_sub FOREIGN KEY(subscription_id) REFERENCES subscriptions(id) ON DELETE SET NULL,INDEX idx_featured(status,starts_at,ends_at)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS lead_wallets (
 user_id BIGINT UNSIGNED PRIMARY KEY,credits INT UNSIGNED NOT NULL DEFAULT 0,updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,CONSTRAINT fk_lead_wallet_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;


-- Production security foundation tables (Phase 2)
CREATE TABLE IF NOT EXISTS schema_migrations (version VARCHAR(80) PRIMARY KEY,applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,checksum_sha256 CHAR(64) NULL) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS auth_tokens (id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,user_id BIGINT UNSIGNED NOT NULL,purpose ENUM('password_reset','email_verify') NOT NULL,selector CHAR(16) NOT NULL,token_hash CHAR(64) NOT NULL,expires_at DATETIME NOT NULL,used_at DATETIME NULL,requested_ip_hash CHAR(64) NULL,created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,UNIQUE KEY uq_auth_token_selector(selector),INDEX idx_auth_token_user(user_id,purpose,used_at,expires_at),CONSTRAINT fk_auth_token_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS auth_rate_limits (bucket_hash CHAR(64) PRIMARY KEY,attempts INT UNSIGNED NOT NULL DEFAULT 0,window_started_at DATETIME NOT NULL,blocked_until DATETIME NULL,updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,INDEX idx_auth_rate_blocked(blocked_until)) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS admin_mfa (user_id BIGINT UNSIGNED PRIMARY KEY,secret_ciphertext TEXT NOT NULL,secret_nonce VARCHAR(128) NOT NULL,encryption_alg VARCHAR(40) NOT NULL,enabled_at DATETIME NOT NULL,last_used_step BIGINT NULL,last_verified_at DATETIME NULL,created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,CONSTRAINT fk_admin_mfa_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE) ENGINE=InnoDB;
INSERT IGNORE INTO schema_migrations(version) VALUES('20260924_001_security_foundation');

-- Production Phase 3: admin-managed payment methods (gateway secrets stay in environment/secrets manager)
CREATE TABLE IF NOT EXISTS payment_methods (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, code VARCHAR(60) NOT NULL UNIQUE, name VARCHAR(120) NOT NULL,
 method_type ENUM('gateway','upi','bank_transfer') NOT NULL, gateway_code VARCHAR(60) NULL,
 audience ENUM('provider','business','both') NOT NULL DEFAULT 'both', currency CHAR(3) NOT NULL DEFAULT 'INR',
 merchant_upi_id VARCHAR(190) NULL, bank_beneficiary VARCHAR(160) NULL, bank_reference VARCHAR(190) NULL,
 display_instructions VARCHAR(2000) NULL, display_order INT UNSIGNED NOT NULL DEFAULT 100, is_active TINYINT(1) NOT NULL DEFAULT 0,
 created_by BIGINT UNSIGNED NOT NULL, updated_by BIGINT UNSIGNED NOT NULL,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 CONSTRAINT fk_payment_method_created_by FOREIGN KEY(created_by) REFERENCES users(id) ON DELETE RESTRICT,
 CONSTRAINT fk_payment_method_updated_by FOREIGN KEY(updated_by) REFERENCES users(id) ON DELETE RESTRICT,
 INDEX idx_payment_method_active(audience,currency,is_active,display_order), INDEX idx_payment_method_type(method_type,gateway_code)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS payment_method_audit (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, payment_method_id BIGINT UNSIGNED NOT NULL, admin_user_id BIGINT UNSIGNED NOT NULL,
 action VARCHAR(40) NOT NULL, before_json JSON NULL, after_json JSON NULL, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT fk_pma_method FOREIGN KEY(payment_method_id) REFERENCES payment_methods(id) ON DELETE RESTRICT,
 CONSTRAINT fk_pma_admin FOREIGN KEY(admin_user_id) REFERENCES users(id) ON DELETE RESTRICT,
 INDEX idx_pma_method(payment_method_id,created_at), INDEX idx_pma_admin(admin_user_id,created_at)
) ENGINE=InnoDB;
ALTER TABLE payments
 ADD COLUMN payment_method_id BIGINT UNSIGNED NULL AFTER subscription_id,
 ADD COLUMN payment_method_code_snapshot VARCHAR(60) NULL AFTER payment_method_id,
 ADD COLUMN payment_method_name_snapshot VARCHAR(120) NULL AFTER payment_method_code_snapshot,
 ADD COLUMN payment_method_type_snapshot VARCHAR(40) NULL AFTER payment_method_name_snapshot,
 ADD CONSTRAINT fk_payment_method FOREIGN KEY(payment_method_id) REFERENCES payment_methods(id) ON DELETE SET NULL,
 ADD INDEX idx_payment_method(payment_method_id,status,created_at);
INSERT IGNORE INTO schema_migrations(version) VALUES('20260924_002_payment_methods');

-- Production Phase 4 checkout/webhook migration
-- LocalConnect production migration 20260924_003
-- Checkout intents, immutable pricing snapshots, gateway webhooks/reconciliation,
-- manual-payment review and subscription entitlement linkage.
-- Non-destructive forward migration. Back up and run preflight first.
USE localconnect_db;

DELIMITER $$
DROP PROCEDURE IF EXISTS lc_add_column_if_missing$$
CREATE PROCEDURE lc_add_column_if_missing(IN p_table VARCHAR(64), IN p_column VARCHAR(64), IN p_definition TEXT)
BEGIN
 IF NOT EXISTS(SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=p_table AND COLUMN_NAME=p_column) THEN
  SET @sql=CONCAT('ALTER TABLE `',p_table,'` ADD COLUMN `',p_column,'` ',p_definition);
  PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
 END IF;
END$$
DELIMITER ;

CALL lc_add_column_if_missing('subscription_plans','billing_period_months','TINYINT UNSIGNED NOT NULL DEFAULT 1 AFTER price_monthly');
CALL lc_add_column_if_missing('subscription_plans','tax_rate_bps','SMALLINT UNSIGNED NOT NULL DEFAULT 0 AFTER billing_period_months');
CALL lc_add_column_if_missing('subscription_plans','tax_label','VARCHAR(40) NOT NULL DEFAULT ''Tax'' AFTER tax_rate_bps');

CALL lc_add_column_if_missing('payments','manual_instructions_snapshot','VARCHAR(2000) NULL AFTER payment_method_type_snapshot');
CALL lc_add_column_if_missing('payments','merchant_upi_id_snapshot','VARCHAR(190) NULL AFTER manual_instructions_snapshot');
CALL lc_add_column_if_missing('payments','bank_beneficiary_snapshot','VARCHAR(160) NULL AFTER merchant_upi_id_snapshot');
CALL lc_add_column_if_missing('payments','bank_reference_snapshot','VARCHAR(190) NULL AFTER bank_beneficiary_snapshot');
CALL lc_add_column_if_missing('payments','plan_id','INT UNSIGNED NULL AFTER subscription_id');
CALL lc_add_column_if_missing('payments','plan_code_snapshot','VARCHAR(40) NULL AFTER plan_id');
CALL lc_add_column_if_missing('payments','plan_name_snapshot','VARCHAR(80) NULL AFTER plan_code_snapshot');
CALL lc_add_column_if_missing('payments','subtotal_amount','DECIMAL(10,2) NULL AFTER plan_name_snapshot');
CALL lc_add_column_if_missing('payments','tax_amount','DECIMAL(10,2) NOT NULL DEFAULT 0 AFTER subtotal_amount');
CALL lc_add_column_if_missing('payments','billing_period_months','TINYINT UNSIGNED NOT NULL DEFAULT 1 AFTER tax_amount');
CALL lc_add_column_if_missing('payments','idempotency_key','CHAR(64) NULL AFTER billing_period_months');
CALL lc_add_column_if_missing('payments','provider_order_id','VARCHAR(190) NULL AFTER provider');
CALL lc_add_column_if_missing('payments','gateway_callback_verified_at','DATETIME NULL AFTER provider_payment_id');
CALL lc_add_column_if_missing('payments','reconciliation_status','ENUM(''pending'',''matched'',''warning'',''manual_review'') NOT NULL DEFAULT ''pending'' AFTER status');
CALL lc_add_column_if_missing('payments','reconciliation_note','VARCHAR(500) NULL AFTER reconciliation_status');
CALL lc_add_column_if_missing('payments','paid_at','DATETIME NULL AFTER reconciliation_note');
CALL lc_add_column_if_missing('payments','failed_at','DATETIME NULL AFTER paid_at');
CALL lc_add_column_if_missing('payments','cancelled_at','DATETIME NULL AFTER failed_at');
CALL lc_add_column_if_missing('payments','refunded_at','DATETIME NULL AFTER cancelled_at');
CALL lc_add_column_if_missing('payments','disputed_at','DATETIME NULL AFTER refunded_at');
CALL lc_add_column_if_missing('payments','invoice_reference','VARCHAR(80) NULL AFTER disputed_at');
CALL lc_add_column_if_missing('payments','checkout_expires_at','DATETIME NULL AFTER invoice_reference');

CALL lc_add_column_if_missing('subscriptions','plan_id','INT UNSIGNED NULL AFTER plan');
CALL lc_add_column_if_missing('subscriptions','source_payment_id','BIGINT UNSIGNED NULL AFTER plan_id');
CALL lc_add_column_if_missing('subscriptions','billing_period_months','TINYINT UNSIGNED NOT NULL DEFAULT 1 AFTER source_payment_id');
CALL lc_add_column_if_missing('subscriptions','invoice_reference','VARCHAR(80) NULL AFTER price');
CALL lc_add_column_if_missing('subscriptions','suspension_reason','VARCHAR(255) NULL AFTER invoice_reference');
CALL lc_add_column_if_missing('subscriptions','benefits_applied_at','DATETIME NULL AFTER suspension_reason');
DROP PROCEDURE IF EXISTS lc_add_column_if_missing;

-- Expanded lifecycle. Re-running these MODIFY statements is safe.
ALTER TABLE payments MODIFY status ENUM('pending','paid','failed','cancelled','refunded','partially_refunded','disputed','requires_review') NOT NULL DEFAULT 'pending';
ALTER TABLE subscriptions MODIFY status ENUM('active','scheduled','expired','cancelled','pending','suspended') NOT NULL DEFAULT 'active';

CREATE TABLE IF NOT EXISTS checkout_intents (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 token_hash CHAR(64) NOT NULL,
 user_id BIGINT UNSIGNED NOT NULL,
 user_role ENUM('provider','business') NOT NULL,
 plan_id INT UNSIGNED NOT NULL,
 plan_code_snapshot VARCHAR(40) NOT NULL,
 plan_name_snapshot VARCHAR(80) NOT NULL,
 currency CHAR(3) NOT NULL DEFAULT 'INR',
 subtotal_amount DECIMAL(10,2) NOT NULL,
 tax_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
 total_amount DECIMAL(10,2) NOT NULL,
 billing_period_months TINYINT UNSIGNED NOT NULL DEFAULT 1,
 status ENUM('selecting_method','pending_gateway','pending_manual','paid','failed','cancelled','expired') NOT NULL DEFAULT 'selecting_method',
 payment_id BIGINT UNSIGNED NULL,
 expires_at DATETIME NOT NULL,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 UNIQUE KEY uq_checkout_token(token_hash),
 INDEX idx_checkout_user(user_id,status,expires_at),
 INDEX idx_checkout_plan(plan_id,status),
 CONSTRAINT fk_checkout_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
 CONSTRAINT fk_checkout_plan FOREIGN KEY(plan_id) REFERENCES subscription_plans(id) ON DELETE RESTRICT,
 CONSTRAINT fk_checkout_payment FOREIGN KEY(payment_id) REFERENCES payments(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS payment_status_history (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 payment_id BIGINT UNSIGNED NOT NULL,
 old_status VARCHAR(40) NULL,
 new_status VARCHAR(40) NOT NULL,
 source ENUM('checkout','callback','webhook','reconciliation','admin','system') NOT NULL,
 external_event_key VARCHAR(190) NULL,
 note VARCHAR(500) NULL,
 actor_user_id BIGINT UNSIGNED NULL,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT fk_psh_payment FOREIGN KEY(payment_id) REFERENCES payments(id) ON DELETE CASCADE,
 CONSTRAINT fk_psh_actor FOREIGN KEY(actor_user_id) REFERENCES users(id) ON DELETE SET NULL,
 INDEX idx_psh_payment(payment_id,created_at),
 INDEX idx_psh_external(external_event_key)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS payment_webhook_events (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 provider VARCHAR(40) NOT NULL,
 event_key VARCHAR(190) NOT NULL,
 event_type VARCHAR(120) NOT NULL,
 payload_sha256 CHAR(64) NOT NULL,
 provider_payment_id VARCHAR(190) NULL,
 provider_order_id VARCHAR(190) NULL,
 signature_valid TINYINT(1) NOT NULL DEFAULT 0,
 processing_status ENUM('received','processed','ignored','failed') NOT NULL DEFAULT 'received',
 processing_note VARCHAR(500) NULL,
 received_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 processed_at DATETIME NULL,
 UNIQUE KEY uq_webhook_event(provider,event_key),
 INDEX idx_webhook_payment(provider_payment_id),
 INDEX idx_webhook_order(provider_order_id),
 INDEX idx_webhook_status(processing_status,received_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS manual_payment_submissions (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 payment_id BIGINT UNSIGNED NOT NULL,
 user_id BIGINT UNSIGNED NOT NULL,
 payer_reference VARCHAR(190) NOT NULL,
 payer_note VARCHAR(500) NULL,
 status ENUM('pending','verified','rejected') NOT NULL DEFAULT 'pending',
 reviewed_by BIGINT UNSIGNED NULL,
 review_note VARCHAR(500) NULL,
 submitted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 reviewed_at DATETIME NULL,
 UNIQUE KEY uq_manual_payment(payment_id),
 INDEX idx_manual_status(status,submitted_at),
 CONSTRAINT fk_manual_payment FOREIGN KEY(payment_id) REFERENCES payments(id) ON DELETE CASCADE,
 CONSTRAINT fk_manual_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
 CONSTRAINT fk_manual_reviewer FOREIGN KEY(reviewed_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

DELIMITER $$
DROP PROCEDURE IF EXISTS lc_phase4_constraints$$
CREATE PROCEDURE lc_phase4_constraints()
BEGIN
 IF NOT EXISTS(SELECT 1 FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='payments' AND INDEX_NAME='uq_payment_idempotency') THEN
  ALTER TABLE payments ADD UNIQUE KEY uq_payment_idempotency(idempotency_key);
 END IF;
 IF NOT EXISTS(SELECT 1 FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='payments' AND INDEX_NAME='uq_payment_provider_order') THEN
  ALTER TABLE payments ADD UNIQUE KEY uq_payment_provider_order(provider,provider_order_id);
 END IF;
 IF NOT EXISTS(SELECT 1 FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='payments' AND INDEX_NAME='uq_payment_provider_payment') THEN
  ALTER TABLE payments ADD UNIQUE KEY uq_payment_provider_payment(provider,provider_payment_id);
 END IF;
 IF NOT EXISTS(SELECT 1 FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='payments' AND INDEX_NAME='idx_payment_reconcile') THEN
  ALTER TABLE payments ADD INDEX idx_payment_reconcile(reconciliation_status,status,created_at);
 END IF;
 IF NOT EXISTS(SELECT 1 FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='subscriptions' AND INDEX_NAME='uq_subscription_source_payment') THEN
  ALTER TABLE subscriptions ADD UNIQUE KEY uq_subscription_source_payment(source_payment_id);
 END IF;
 IF NOT EXISTS(SELECT 1 FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='subscriptions' AND INDEX_NAME='idx_subscription_schedule') THEN
  ALTER TABLE subscriptions ADD INDEX idx_subscription_schedule(user_id,status,starts_at,ends_at);
 END IF;
 IF NOT EXISTS(SELECT 1 FROM information_schema.TABLE_CONSTRAINTS WHERE CONSTRAINT_SCHEMA=DATABASE() AND TABLE_NAME='payments' AND CONSTRAINT_NAME='fk_payment_plan') THEN
  ALTER TABLE payments ADD CONSTRAINT fk_payment_plan FOREIGN KEY(plan_id) REFERENCES subscription_plans(id) ON DELETE RESTRICT;
 END IF;
 IF NOT EXISTS(SELECT 1 FROM information_schema.TABLE_CONSTRAINTS WHERE CONSTRAINT_SCHEMA=DATABASE() AND TABLE_NAME='subscriptions' AND CONSTRAINT_NAME='fk_subscription_plan') THEN
  ALTER TABLE subscriptions ADD CONSTRAINT fk_subscription_plan FOREIGN KEY(plan_id) REFERENCES subscription_plans(id) ON DELETE RESTRICT;
 END IF;
 IF NOT EXISTS(SELECT 1 FROM information_schema.TABLE_CONSTRAINTS WHERE CONSTRAINT_SCHEMA=DATABASE() AND TABLE_NAME='subscriptions' AND CONSTRAINT_NAME='fk_subscription_source_payment') THEN
  ALTER TABLE subscriptions ADD CONSTRAINT fk_subscription_source_payment FOREIGN KEY(source_payment_id) REFERENCES payments(id) ON DELETE RESTRICT;
 END IF;
END$$
DELIMITER ;
CALL lc_phase4_constraints();
DROP PROCEDURE IF EXISTS lc_phase4_constraints;

INSERT IGNORE INTO schema_migrations(version,checksum_sha256) VALUES('20260924_003_checkout_webhooks',NULL);


-- Production Phase 5 performance/reliability additions
-- LocalConnect production migration 20260924_004
-- Phase 5: bounded-list supporting indexes and bounded payment reconciliation queue.
-- Forward-only/non-destructive. Run production preflight and take a backup first.

CREATE TABLE IF NOT EXISTS payment_reconciliation_jobs (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 webhook_event_id BIGINT UNSIGNED NULL,
 payment_id BIGINT UNSIGNED NULL,
 status ENUM('queued','processing','retry','done','dead') NOT NULL DEFAULT 'queued',
 attempts TINYINT UNSIGNED NOT NULL DEFAULT 0,
 max_attempts TINYINT UNSIGNED NOT NULL DEFAULT 5,
 next_attempt_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 locked_at DATETIME NULL,
 last_error VARCHAR(500) NULL,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 UNIQUE KEY uq_reconcile_webhook_event(webhook_event_id),
 INDEX idx_reconcile_due(status,next_attempt_at,id),
 INDEX idx_reconcile_payment(payment_id,status),
 CONSTRAINT fk_reconcile_webhook FOREIGN KEY(webhook_event_id) REFERENCES payment_webhook_events(id) ON DELETE CASCADE,
 CONSTRAINT fk_reconcile_payment FOREIGN KEY(payment_id) REFERENCES payments(id) ON DELETE CASCADE
) ENGINE=InnoDB;

DELIMITER $$
DROP PROCEDURE IF EXISTS lc_phase5_add_index$$
CREATE PROCEDURE lc_phase5_add_index(IN p_table VARCHAR(64), IN p_index VARCHAR(64), IN p_columns TEXT)
BEGIN
 IF NOT EXISTS(SELECT 1 FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=p_table AND INDEX_NAME=p_index) THEN
  SET @sql=CONCAT('ALTER TABLE `',p_table,'` ADD INDEX `',p_index,'` (',p_columns,')');
  PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
 END IF;
END$$
DELIMITER ;

CALL lc_phase5_add_index('service_requests','idx_sr_provider_created','provider_id,created_at,id');
CALL lc_phase5_add_index('service_requests','idx_sr_business_created','business_id,created_at,id');
CALL lc_phase5_add_index('service_requests','idx_sr_customer_created','customer_id,created_at,id');
CALL lc_phase5_add_index('service_requests','idx_sr_requirement_feed','request_type,status,created_at,id,service_id');
CALL lc_phase5_add_index('reviews','idx_reviews_customer_created','customer_id,created_at,id');
CALL lc_phase5_add_index('reviews','idx_reviews_target_created','target_user_id,status,created_at,id');
CALL lc_phase5_add_index('favorites','idx_favorites_customer_created','customer_id,created_at,id');
CALL lc_phase5_add_index('portfolio_images','idx_portfolio_user_created_id','user_id,created_at,id');
CALL lc_phase5_add_index('reports','idx_reports_created','created_at,id');
CALL lc_phase5_add_index('users','idx_users_role_status_id','role,status,id');
DROP PROCEDURE IF EXISTS lc_phase5_add_index;

INSERT IGNORE INTO schema_migrations(version) VALUES('20260924_004_performance_reliability');

-- Production Phase 6 deployment-hardening support indexes
DELIMITER $$
DROP PROCEDURE IF EXISTS lc_add_index_if_missing$$
CREATE PROCEDURE lc_add_index_if_missing(IN p_table VARCHAR(64), IN p_index VARCHAR(64), IN p_columns TEXT)
BEGIN
 IF NOT EXISTS(SELECT 1 FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=p_table AND INDEX_NAME=p_index) THEN
  SET @sql=CONCAT('ALTER TABLE `',p_table,'` ADD INDEX `',p_index,'` (',p_columns,')');
  PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
 END IF;
END$$
DELIMITER ;
CALL lc_add_index_if_missing('auth_tokens','idx_auth_token_expiry','purpose,used_at,expires_at');
CALL lc_add_index_if_missing('platform_activity','idx_activity_actor_created','actor_id,created_at');
CALL lc_add_index_if_missing('checkout_intents','idx_checkout_expiry','status,expires_at');
CALL lc_add_index_if_missing('payment_reconciliation_jobs','idx_reconcile_payment_due','payment_id,status,next_attempt_at');
DROP PROCEDURE IF EXISTS lc_add_index_if_missing;
INSERT IGNORE INTO schema_migrations(version,checksum_sha256) VALUES('20260924_005_production_hardening',NULL);
