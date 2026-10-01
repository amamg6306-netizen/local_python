-- LocalConnect PostgreSQL schema generated from SQLAlchemy models.
-- Do not edit manually; regenerate after model schema changes.
BEGIN;

CREATE TYPE subscription_plan_audience AS ENUM ('provider', 'business', 'both');

CREATE TYPE subscription_legacy_plan AS ENUM ('free', 'professional', 'business');

CREATE TYPE subscription_status AS ENUM ('active', 'scheduled', 'expired', 'cancelled', 'pending', 'suspended');

CREATE TYPE payment_method_type AS ENUM ('gateway', 'upi', 'bank_transfer');

CREATE TYPE payment_method_audience AS ENUM ('provider', 'business', 'both');

CREATE TYPE payment_status AS ENUM ('pending', 'paid', 'failed', 'cancelled', 'refunded', 'partially_refunded', 'disputed', 'requires_review');

CREATE TYPE payment_reconciliation_status AS ENUM ('pending', 'matched', 'warning', 'manual_review');

CREATE TYPE checkout_user_role AS ENUM ('provider', 'business');

CREATE TYPE checkout_status AS ENUM ('selecting_method', 'pending_gateway', 'pending_manual', 'paid', 'failed', 'cancelled', 'expired');

CREATE TYPE payment_status_source AS ENUM ('checkout', 'callback', 'webhook', 'reconciliation', 'admin', 'system');

CREATE TYPE webhook_processing_status AS ENUM ('received', 'processed', 'ignored', 'failed');

CREATE TYPE manual_payment_status AS ENUM ('pending', 'verified', 'rejected');

CREATE TYPE reconciliation_job_status AS ENUM ('queued', 'processing', 'retry', 'done', 'dead');

CREATE TYPE featured_listing_status AS ENUM ('pending', 'active', 'expired', 'cancelled');

CREATE TYPE advertisement_status AS ENUM ('draft', 'active', 'paused', 'expired');

CREATE TYPE user_role AS ENUM ('customer', 'provider', 'business', 'admin');

CREATE TYPE user_status AS ENUM ('active', 'blocked', 'pending');

CREATE TYPE provider_availability AS ENUM ('available', 'busy', 'unavailable');

CREATE TYPE provider_verification AS ENUM ('pending', 'verified', 'rejected');

CREATE TYPE business_verification AS ENUM ('pending', 'verified', 'rejected');

CREATE TYPE request_type AS ENUM ('direct', 'requirement');

CREATE TYPE request_status AS ENUM ('pending', 'accepted', 'rejected', 'in_progress', 'completed', 'cancelled');

CREATE TYPE request_history_status AS ENUM ('pending', 'accepted', 'rejected', 'in_progress', 'completed', 'cancelled');

CREATE TYPE review_status AS ENUM ('published', 'hidden', 'removed');

CREATE TYPE report_target_type AS ENUM ('provider', 'business', 'review');

CREATE TYPE report_reason AS ENUM ('fake_profile', 'wrong_information', 'spam', 'fraud_concern', 'inappropriate_content', 'other');

CREATE TYPE report_status AS ENUM ('open', 'investigating', 'resolved', 'dismissed');

CREATE TYPE auth_token_purpose AS ENUM ('password_reset', 'email_verify');

CREATE TABLE subscription_plans (
	id SERIAL NOT NULL, 
	code VARCHAR(40) NOT NULL, 
	name VARCHAR(80) NOT NULL, 
	audience subscription_plan_audience DEFAULT 'both' NOT NULL, 
	price_monthly NUMERIC(10, 2) DEFAULT '0' NOT NULL, 
	billing_period_months SMALLINT DEFAULT '1' NOT NULL, 
	tax_rate_bps SMALLINT DEFAULT '0' NOT NULL, 
	tax_label VARCHAR(40) DEFAULT 'Tax' NOT NULL, 
	featured_days INTEGER DEFAULT '0' NOT NULL, 
	lead_limit INTEGER, 
	description VARCHAR(255), 
	is_active SMALLINT DEFAULT '1' NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (code)
);

CREATE TABLE subscriptions (
	id BIGSERIAL NOT NULL, 
	user_id BIGINT NOT NULL, 
	plan subscription_legacy_plan DEFAULT 'free' NOT NULL, 
	plan_id INTEGER, 
	source_payment_id BIGINT, 
	billing_period_months SMALLINT DEFAULT '1' NOT NULL, 
	status subscription_status DEFAULT 'active' NOT NULL, 
	starts_at TIMESTAMP WITHOUT TIME ZONE, 
	ends_at TIMESTAMP WITHOUT TIME ZONE, 
	price NUMERIC(10, 2) DEFAULT '0' NOT NULL, 
	invoice_reference VARCHAR(80), 
	suspension_reason VARCHAR(255), 
	benefits_applied_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_subscription_source_payment UNIQUE (source_payment_id)
);

CREATE INDEX idx_subscription_schedule ON subscriptions (user_id, status, starts_at, ends_at);

CREATE INDEX idx_subscription_user ON subscriptions (user_id, status);

CREATE TABLE payments (
	id BIGSERIAL NOT NULL, 
	user_id BIGINT NOT NULL, 
	subscription_id BIGINT, 
	plan_id INTEGER, 
	payment_method_id BIGINT, 
	payment_method_code_snapshot VARCHAR(60), 
	payment_method_name_snapshot VARCHAR(120), 
	payment_method_type_snapshot VARCHAR(40), 
	manual_instructions_snapshot VARCHAR(2000), 
	merchant_upi_id_snapshot VARCHAR(190), 
	bank_beneficiary_snapshot VARCHAR(160), 
	bank_reference_snapshot VARCHAR(190), 
	plan_code_snapshot VARCHAR(40), 
	plan_name_snapshot VARCHAR(80), 
	subtotal_amount NUMERIC(10, 2), 
	tax_amount NUMERIC(10, 2) DEFAULT '0' NOT NULL, 
	billing_period_months SMALLINT DEFAULT '1' NOT NULL, 
	idempotency_key VARCHAR(64), 
	provider VARCHAR(50), 
	provider_order_id VARCHAR(190), 
	provider_payment_id VARCHAR(190), 
	gateway_callback_verified_at TIMESTAMP WITHOUT TIME ZONE, 
	amount NUMERIC(10, 2) NOT NULL, 
	currency VARCHAR(3) DEFAULT 'INR' NOT NULL, 
	status payment_status DEFAULT 'pending' NOT NULL, 
	reconciliation_status payment_reconciliation_status DEFAULT 'pending' NOT NULL, 
	reconciliation_note VARCHAR(500), 
	paid_at TIMESTAMP WITHOUT TIME ZONE, 
	failed_at TIMESTAMP WITHOUT TIME ZONE, 
	cancelled_at TIMESTAMP WITHOUT TIME ZONE, 
	refunded_at TIMESTAMP WITHOUT TIME ZONE, 
	disputed_at TIMESTAMP WITHOUT TIME ZONE, 
	invoice_reference VARCHAR(80), 
	checkout_expires_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_payment_idempotency UNIQUE (idempotency_key), 
	CONSTRAINT uq_payment_provider_order UNIQUE (provider, provider_order_id), 
	CONSTRAINT uq_payment_provider_payment UNIQUE (provider, provider_payment_id)
);

CREATE INDEX idx_payment_method ON payments (payment_method_id, status, created_at);

CREATE INDEX idx_payment_reconcile ON payments (reconciliation_status, status, created_at);

CREATE INDEX idx_payment_status ON payments (status, created_at);

CREATE TABLE payment_webhook_events (
	id BIGSERIAL NOT NULL, 
	provider VARCHAR(40) NOT NULL, 
	event_key VARCHAR(190) NOT NULL, 
	event_type VARCHAR(120) NOT NULL, 
	payload_sha256 VARCHAR(64) NOT NULL, 
	provider_payment_id VARCHAR(190), 
	provider_order_id VARCHAR(190), 
	signature_valid SMALLINT DEFAULT '0' NOT NULL, 
	processing_status webhook_processing_status DEFAULT 'received' NOT NULL, 
	processing_note VARCHAR(500), 
	received_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	processed_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_webhook_event UNIQUE (provider, event_key)
);

CREATE INDEX idx_webhook_status ON payment_webhook_events (processing_status, received_at);

CREATE INDEX idx_webhook_payment ON payment_webhook_events (provider_payment_id);

CREATE INDEX idx_webhook_order ON payment_webhook_events (provider_order_id);

CREATE TABLE users (
	id BIGSERIAL NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	email VARCHAR(190) NOT NULL, 
	phone VARCHAR(25), 
	password_hash VARCHAR(255) NOT NULL, 
	role user_role DEFAULT 'customer' NOT NULL, 
	status user_status DEFAULT 'active' NOT NULL, 
	profile_image VARCHAR(255), 
	city VARCHAR(100), 
	state VARCHAR(100), 
	area VARCHAR(150), 
	pincode VARCHAR(12), 
	latitude NUMERIC(10, 7), 
	longitude NUMERIC(10, 7), 
	last_login_at TIMESTAMP WITHOUT TIME ZONE, 
	email_verified_at TIMESTAMP WITHOUT TIME ZONE, 
	session_version INTEGER DEFAULT '1' NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (email)
);

CREATE INDEX idx_users_role_status_id ON users (role, status, id);

CREATE INDEX idx_users_role_status ON users (role, status);

CREATE INDEX idx_users_location ON users (city, state, area);

CREATE INDEX idx_users_name ON users (name);

CREATE TABLE categories (
	id SERIAL NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	slug VARCHAR(140) NOT NULL, 
	icon VARCHAR(80), 
	description VARCHAR(255), 
	is_active SMALLINT DEFAULT '1' NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	UNIQUE (slug)
);

CREATE INDEX idx_categories_active ON categories (is_active);

CREATE TABLE schema_migrations (
	version VARCHAR(80) NOT NULL, 
	applied_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	checksum_sha256 VARCHAR(64), 
	PRIMARY KEY (version)
);

CREATE TABLE auth_rate_limits (
	bucket_hash VARCHAR(64) NOT NULL, 
	attempts INTEGER DEFAULT '0' NOT NULL, 
	window_started_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	blocked_until TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (bucket_hash)
);

CREATE INDEX idx_auth_rate_blocked ON auth_rate_limits (blocked_until);

CREATE TABLE payment_methods (
	id BIGSERIAL NOT NULL, 
	code VARCHAR(60) NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	method_type payment_method_type NOT NULL, 
	gateway_code VARCHAR(60), 
	audience payment_method_audience DEFAULT 'both' NOT NULL, 
	currency VARCHAR(3) DEFAULT 'INR' NOT NULL, 
	merchant_upi_id VARCHAR(190), 
	bank_beneficiary VARCHAR(160), 
	bank_reference VARCHAR(190), 
	display_instructions VARCHAR(2000), 
	display_order INTEGER DEFAULT '100' NOT NULL, 
	is_active SMALLINT DEFAULT '0' NOT NULL, 
	created_by BIGINT NOT NULL, 
	updated_by BIGINT NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (code), 
	CONSTRAINT fk_payment_method_created_by FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE RESTRICT, 
	CONSTRAINT fk_payment_method_updated_by FOREIGN KEY(updated_by) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE INDEX idx_payment_method_type ON payment_methods (method_type, gateway_code);

CREATE INDEX idx_payment_method_active ON payment_methods (audience, currency, is_active, display_order);

CREATE TABLE checkout_intents (
	id BIGSERIAL NOT NULL, 
	token_hash VARCHAR(64) NOT NULL, 
	user_id BIGINT NOT NULL, 
	user_role checkout_user_role NOT NULL, 
	plan_id INTEGER NOT NULL, 
	plan_code_snapshot VARCHAR(40) NOT NULL, 
	plan_name_snapshot VARCHAR(80) NOT NULL, 
	currency VARCHAR(3) DEFAULT 'INR' NOT NULL, 
	subtotal_amount NUMERIC(10, 2) NOT NULL, 
	tax_amount NUMERIC(10, 2) DEFAULT '0' NOT NULL, 
	total_amount NUMERIC(10, 2) NOT NULL, 
	billing_period_months SMALLINT DEFAULT '1' NOT NULL, 
	status checkout_status DEFAULT 'selecting_method' NOT NULL, 
	payment_id BIGINT, 
	expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_checkout_token UNIQUE (token_hash), 
	CONSTRAINT fk_checkout_user FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	CONSTRAINT fk_checkout_plan FOREIGN KEY(plan_id) REFERENCES subscription_plans (id) ON DELETE RESTRICT, 
	CONSTRAINT fk_checkout_payment FOREIGN KEY(payment_id) REFERENCES payments (id) ON DELETE SET NULL
);

CREATE INDEX idx_checkout_expiry ON checkout_intents (status, expires_at);

CREATE INDEX idx_checkout_user ON checkout_intents (user_id, status, expires_at);

CREATE INDEX idx_checkout_plan ON checkout_intents (plan_id, status);

CREATE TABLE payment_status_history (
	id BIGSERIAL NOT NULL, 
	payment_id BIGINT NOT NULL, 
	old_status VARCHAR(40), 
	new_status VARCHAR(40) NOT NULL, 
	source payment_status_source NOT NULL, 
	external_event_key VARCHAR(190), 
	note VARCHAR(500), 
	actor_user_id BIGINT, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_psh_payment FOREIGN KEY(payment_id) REFERENCES payments (id) ON DELETE CASCADE, 
	CONSTRAINT fk_psh_actor FOREIGN KEY(actor_user_id) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX idx_psh_external ON payment_status_history (external_event_key);

CREATE INDEX idx_psh_payment ON payment_status_history (payment_id, created_at);

CREATE TABLE manual_payment_submissions (
	id BIGSERIAL NOT NULL, 
	payment_id BIGINT NOT NULL, 
	user_id BIGINT NOT NULL, 
	payer_reference VARCHAR(190) NOT NULL, 
	payer_note VARCHAR(500), 
	status manual_payment_status DEFAULT 'pending' NOT NULL, 
	reviewed_by BIGINT, 
	review_note VARCHAR(500), 
	submitted_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	reviewed_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_manual_payment UNIQUE (payment_id), 
	CONSTRAINT fk_manual_payment FOREIGN KEY(payment_id) REFERENCES payments (id) ON DELETE CASCADE, 
	CONSTRAINT fk_manual_user FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	CONSTRAINT fk_manual_reviewer FOREIGN KEY(reviewed_by) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX idx_manual_status ON manual_payment_submissions (status, submitted_at);

CREATE TABLE payment_reconciliation_jobs (
	id BIGSERIAL NOT NULL, 
	webhook_event_id BIGINT, 
	payment_id BIGINT, 
	status reconciliation_job_status DEFAULT 'queued' NOT NULL, 
	attempts SMALLINT DEFAULT '0' NOT NULL, 
	max_attempts SMALLINT DEFAULT '5' NOT NULL, 
	next_attempt_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	locked_at TIMESTAMP WITHOUT TIME ZONE, 
	last_error VARCHAR(500), 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_reconcile_webhook_event UNIQUE (webhook_event_id), 
	CONSTRAINT fk_reconcile_webhook FOREIGN KEY(webhook_event_id) REFERENCES payment_webhook_events (id) ON DELETE CASCADE, 
	CONSTRAINT fk_reconcile_payment FOREIGN KEY(payment_id) REFERENCES payments (id) ON DELETE CASCADE
);

CREATE INDEX idx_reconcile_payment ON payment_reconciliation_jobs (payment_id, status);

CREATE INDEX idx_reconcile_payment_due ON payment_reconciliation_jobs (payment_id, status, next_attempt_at);

CREATE INDEX idx_reconcile_due ON payment_reconciliation_jobs (status, next_attempt_at, id);

CREATE TABLE featured_listings (
	id BIGSERIAL NOT NULL, 
	user_id BIGINT NOT NULL, 
	subscription_id BIGINT, 
	status featured_listing_status DEFAULT 'pending' NOT NULL, 
	starts_at TIMESTAMP WITHOUT TIME ZONE, 
	ends_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_featured_user FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	CONSTRAINT fk_featured_sub FOREIGN KEY(subscription_id) REFERENCES subscriptions (id) ON DELETE SET NULL
);

CREATE INDEX idx_featured ON featured_listings (status, starts_at, ends_at);

CREATE TABLE lead_wallets (
	user_id BIGINT NOT NULL, 
	credits INTEGER DEFAULT '0' NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (user_id), 
	CONSTRAINT fk_lead_wallet_user FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE advertisements (
	id BIGSERIAL NOT NULL, 
	title VARCHAR(180) NOT NULL, 
	description VARCHAR(500), 
	image VARCHAR(255), 
	target_url VARCHAR(255), 
	placement VARCHAR(80), 
	budget NUMERIC(10, 2) DEFAULT '0' NOT NULL, 
	impressions INTEGER DEFAULT '0' NOT NULL, 
	clicks INTEGER DEFAULT '0' NOT NULL, 
	status advertisement_status DEFAULT 'draft' NOT NULL, 
	starts_at TIMESTAMP WITHOUT TIME ZONE, 
	ends_at TIMESTAMP WITHOUT TIME ZONE, 
	created_by BIGINT NOT NULL, 
	sponsor_user_id BIGINT, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_ad_admin FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE RESTRICT, 
	CONSTRAINT fk_ad_sponsor FOREIGN KEY(sponsor_user_id) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX idx_ads_status ON advertisements (status, starts_at, ends_at);

CREATE TABLE locations (
	id BIGSERIAL NOT NULL, 
	user_id BIGINT NOT NULL, 
	label VARCHAR(80) DEFAULT 'Primary', 
	address_line VARCHAR(255), 
	area VARCHAR(150), 
	city VARCHAR(100) NOT NULL, 
	state VARCHAR(100) NOT NULL, 
	pincode VARCHAR(12), 
	latitude NUMERIC(10, 7), 
	longitude NUMERIC(10, 7), 
	is_default SMALLINT DEFAULT '0' NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_locations_user FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX idx_locations_city ON locations (city, state, area);

CREATE TABLE platform_activity (
	id BIGSERIAL NOT NULL, 
	actor_id BIGINT, 
	action VARCHAR(100) NOT NULL, 
	target_type VARCHAR(60), 
	target_id BIGINT, 
	details VARCHAR(500), 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_activity_actor FOREIGN KEY(actor_id) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX idx_activity_actor_created ON platform_activity (actor_id, created_at);

CREATE INDEX idx_activity_created ON platform_activity (created_at);

CREATE INDEX idx_activity_action ON platform_activity (action);

CREATE TABLE provider_profiles (
	id BIGSERIAL NOT NULL, 
	user_id BIGINT NOT NULL, 
	headline VARCHAR(180), 
	about TEXT, 
	experience_years SMALLINT DEFAULT '0', 
	service_area VARCHAR(255), 
	price_min NUMERIC(10, 2), 
	price_max NUMERIC(10, 2), 
	availability_status provider_availability DEFAULT 'available' NOT NULL, 
	working_hours VARCHAR(255), 
	verification_status provider_verification DEFAULT 'pending' NOT NULL, 
	verified_at TIMESTAMP WITHOUT TIME ZONE, 
	is_featured SMALLINT DEFAULT '0' NOT NULL, 
	profile_views INTEGER DEFAULT '0' NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	CONSTRAINT fk_provider_user FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX idx_provider_verify ON provider_profiles (verification_status);

CREATE INDEX idx_provider_available ON provider_profiles (availability_status);

CREATE TABLE business_profiles (
	id BIGSERIAL NOT NULL, 
	user_id BIGINT NOT NULL, 
	category_id INTEGER, 
	business_name VARCHAR(180), 
	slug VARCHAR(200), 
	logo VARCHAR(255), 
	description TEXT, 
	address VARCHAR(255), 
	phone VARCHAR(25), 
	opening_time TIME WITHOUT TIME ZONE, 
	closing_time TIME WITHOUT TIME ZONE, 
	price_min NUMERIC(10, 2), 
	price_max NUMERIC(10, 2), 
	website VARCHAR(255), 
	social_links JSON, 
	verification_status business_verification DEFAULT 'pending' NOT NULL, 
	verified_at TIMESTAMP WITHOUT TIME ZONE, 
	is_featured SMALLINT DEFAULT '0' NOT NULL, 
	profile_views INTEGER DEFAULT '0' NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	CONSTRAINT fk_business_user FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	CONSTRAINT fk_business_category FOREIGN KEY(category_id) REFERENCES categories (id) ON DELETE SET NULL, 
	UNIQUE (slug)
);

CREATE INDEX idx_business_verify ON business_profiles (verification_status);

CREATE INDEX idx_business_name ON business_profiles (business_name);

CREATE TABLE services (
	id BIGSERIAL NOT NULL, 
	category_id INTEGER NOT NULL, 
	name VARCHAR(160) NOT NULL, 
	slug VARCHAR(180) NOT NULL, 
	description TEXT, 
	is_active SMALLINT DEFAULT '1' NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_service_category_slug UNIQUE (category_id, slug), 
	CONSTRAINT fk_services_category FOREIGN KEY(category_id) REFERENCES categories (id) ON DELETE RESTRICT
);

CREATE INDEX idx_service_name ON services (name);

CREATE TABLE portfolio_images (
	id BIGSERIAL NOT NULL, 
	user_id BIGINT NOT NULL, 
	image_path VARCHAR(255) NOT NULL, 
	caption VARCHAR(255), 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_portfolio_user FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX idx_portfolio_user ON portfolio_images (user_id, created_at);

CREATE INDEX idx_portfolio_user_created_id ON portfolio_images (user_id, created_at, id);

CREATE TABLE favorites (
	id BIGSERIAL NOT NULL, 
	customer_id BIGINT NOT NULL, 
	target_user_id BIGINT NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_favorite UNIQUE (customer_id, target_user_id), 
	CONSTRAINT fk_fav_customer FOREIGN KEY(customer_id) REFERENCES users (id) ON DELETE CASCADE, 
	CONSTRAINT fk_fav_target FOREIGN KEY(target_user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX idx_favorites_customer_created ON favorites (customer_id, created_at, id);

CREATE TABLE notifications (
	id BIGSERIAL NOT NULL, 
	user_id BIGINT NOT NULL, 
	type VARCHAR(80) NOT NULL, 
	title VARCHAR(180) NOT NULL, 
	message VARCHAR(500) NOT NULL, 
	link VARCHAR(255), 
	is_read SMALLINT DEFAULT '0' NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_notification_user FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX idx_notifications_user ON notifications (user_id, is_read, created_at);

CREATE TABLE reports (
	id BIGSERIAL NOT NULL, 
	reporter_id BIGINT NOT NULL, 
	target_type report_target_type NOT NULL, 
	target_id BIGINT NOT NULL, 
	reason report_reason NOT NULL, 
	details TEXT, 
	status report_status DEFAULT 'open' NOT NULL, 
	resolved_by BIGINT, 
	resolution_note VARCHAR(500), 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_reporter FOREIGN KEY(reporter_id) REFERENCES users (id) ON DELETE CASCADE, 
	CONSTRAINT fk_report_admin FOREIGN KEY(resolved_by) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX idx_reports_status ON reports (status);

CREATE INDEX idx_reports_created ON reports (created_at, id);

CREATE TABLE auth_tokens (
	id BIGSERIAL NOT NULL, 
	user_id BIGINT NOT NULL, 
	purpose auth_token_purpose NOT NULL, 
	selector VARCHAR(16) NOT NULL, 
	token_hash VARCHAR(64) NOT NULL, 
	expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	used_at TIMESTAMP WITHOUT TIME ZONE, 
	requested_ip_hash VARCHAR(64), 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_auth_token_selector UNIQUE (selector), 
	CONSTRAINT fk_auth_token_user FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX idx_auth_token_user ON auth_tokens (user_id, purpose, used_at, expires_at);

CREATE INDEX idx_auth_token_expiry ON auth_tokens (purpose, used_at, expires_at);

CREATE TABLE admin_mfa (
	user_id BIGINT NOT NULL, 
	secret_ciphertext TEXT NOT NULL, 
	secret_nonce VARCHAR(128) NOT NULL, 
	encryption_alg VARCHAR(40) NOT NULL, 
	enabled_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	last_used_step BIGINT, 
	last_verified_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (user_id), 
	CONSTRAINT fk_admin_mfa_user FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE payment_method_audit (
	id BIGSERIAL NOT NULL, 
	payment_method_id BIGINT NOT NULL, 
	admin_user_id BIGINT NOT NULL, 
	action VARCHAR(40) NOT NULL, 
	before_json JSON, 
	after_json JSON, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_pma_method FOREIGN KEY(payment_method_id) REFERENCES payment_methods (id) ON DELETE RESTRICT, 
	CONSTRAINT fk_pma_admin FOREIGN KEY(admin_user_id) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE INDEX idx_pma_method ON payment_method_audit (payment_method_id, created_at);

CREATE INDEX idx_pma_admin ON payment_method_audit (admin_user_id, created_at);

CREATE TABLE provider_services (
	id BIGSERIAL NOT NULL, 
	provider_user_id BIGINT NOT NULL, 
	service_id BIGINT NOT NULL, 
	title VARCHAR(180), 
	description TEXT, 
	price_from NUMERIC(10, 2), 
	price_to NUMERIC(10, 2), 
	is_active SMALLINT DEFAULT '1' NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_provider_service UNIQUE (provider_user_id, service_id), 
	CONSTRAINT fk_ps_user FOREIGN KEY(provider_user_id) REFERENCES users (id) ON DELETE CASCADE, 
	CONSTRAINT fk_ps_service FOREIGN KEY(service_id) REFERENCES services (id) ON DELETE CASCADE
);

CREATE INDEX idx_ps_active ON provider_services (is_active);

CREATE TABLE service_requests (
	id BIGSERIAL NOT NULL, 
	customer_id BIGINT NOT NULL, 
	provider_id BIGINT, 
	business_id BIGINT, 
	category_id INTEGER NOT NULL, 
	service_id BIGINT, 
	request_type request_type DEFAULT 'direct' NOT NULL, 
	title VARCHAR(180) NOT NULL, 
	description TEXT NOT NULL, 
	location_text VARCHAR(255) NOT NULL, 
	preferred_date DATE, 
	preferred_time TIME WITHOUT TIME ZONE, 
	budget_min NUMERIC(10, 2), 
	budget_max NUMERIC(10, 2), 
	additional_notes TEXT, 
	status request_status DEFAULT 'pending' NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_sr_customer FOREIGN KEY(customer_id) REFERENCES users (id) ON DELETE CASCADE, 
	CONSTRAINT fk_sr_provider FOREIGN KEY(provider_id) REFERENCES users (id) ON DELETE SET NULL, 
	CONSTRAINT fk_sr_business FOREIGN KEY(business_id) REFERENCES users (id) ON DELETE SET NULL, 
	CONSTRAINT fk_sr_category FOREIGN KEY(category_id) REFERENCES categories (id), 
	CONSTRAINT fk_sr_service FOREIGN KEY(service_id) REFERENCES services (id) ON DELETE SET NULL
);

CREATE INDEX idx_sr_requirement_feed ON service_requests (request_type, status, created_at, id, service_id);

CREATE INDEX idx_sr_provider_created ON service_requests (provider_id, created_at, id);

CREATE INDEX idx_sr_status ON service_requests (status);

CREATE INDEX idx_sr_category ON service_requests (category_id, status);

CREATE INDEX idx_sr_business_created ON service_requests (business_id, created_at, id);

CREATE INDEX idx_sr_type_status_service ON service_requests (request_type, status, service_id);

CREATE INDEX idx_sr_provider ON service_requests (provider_id, status);

CREATE INDEX idx_sr_customer_created ON service_requests (customer_id, created_at, id);

CREATE INDEX idx_sr_business ON service_requests (business_id, status);

CREATE INDEX idx_sr_customer ON service_requests (customer_id, status);

CREATE TABLE request_status_history (
	id BIGSERIAL NOT NULL, 
	request_id BIGINT NOT NULL, 
	status request_history_status NOT NULL, 
	changed_by BIGINT NOT NULL, 
	note VARCHAR(500), 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_rsh_request FOREIGN KEY(request_id) REFERENCES service_requests (id) ON DELETE CASCADE, 
	CONSTRAINT fk_rsh_user FOREIGN KEY(changed_by) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX idx_rsh_request ON request_status_history (request_id, created_at);

CREATE TABLE reviews (
	id BIGSERIAL NOT NULL, 
	request_id BIGINT NOT NULL, 
	customer_id BIGINT NOT NULL, 
	target_user_id BIGINT NOT NULL, 
	rating SMALLINT NOT NULL, 
	comment TEXT, 
	status review_status DEFAULT 'published' NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT chk_rating CHECK (rating BETWEEN 1 AND 5), 
	UNIQUE (request_id), 
	CONSTRAINT fk_review_request FOREIGN KEY(request_id) REFERENCES service_requests (id) ON DELETE CASCADE, 
	CONSTRAINT fk_review_customer FOREIGN KEY(customer_id) REFERENCES users (id) ON DELETE CASCADE, 
	CONSTRAINT fk_review_target FOREIGN KEY(target_user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX idx_reviews_target_created ON reviews (target_user_id, status, created_at, id);

CREATE INDEX idx_reviews_customer_created ON reviews (customer_id, created_at, id);

CREATE INDEX idx_reviews_target ON reviews (target_user_id, status);

ALTER TABLE payments ADD CONSTRAINT fk_payment_method FOREIGN KEY(payment_method_id) REFERENCES payment_methods (id) ON DELETE SET NULL;

ALTER TABLE subscriptions ADD CONSTRAINT fk_subscription_plan FOREIGN KEY(plan_id) REFERENCES subscription_plans (id) ON DELETE RESTRICT;

ALTER TABLE payments ADD CONSTRAINT fk_payment_plan FOREIGN KEY(plan_id) REFERENCES subscription_plans (id) ON DELETE RESTRICT;

ALTER TABLE payments ADD CONSTRAINT fk_payment_sub FOREIGN KEY(subscription_id) REFERENCES subscriptions (id) ON DELETE SET NULL;

ALTER TABLE subscriptions ADD CONSTRAINT fk_subscription_user FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE;

ALTER TABLE payments ADD CONSTRAINT fk_payment_user FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE;

ALTER TABLE subscriptions ADD CONSTRAINT fk_subscription_source_payment FOREIGN KEY(source_payment_id) REFERENCES payments (id) ON DELETE RESTRICT;

COMMIT;

-- Reference catalogue required by the application.
INSERT INTO categories (name, slug, icon) VALUES
('Home Services','home-services','fa-house'),
('Electrical','electrical','fa-bolt'),
('Plumbing','plumbing','fa-faucet-drip'),
('Carpenter','carpenter','fa-hammer'),
('Painting','painting','fa-paint-roller'),
('Cleaning','cleaning','fa-broom'),
('Appliance Repair','appliance-repair','fa-screwdriver-wrench'),
('AC & Cooling','ac-cooling','fa-snowflake'),
('Computer & Mobile Repair','computer-mobile-repair','fa-laptop'),
('Automotive','automotive','fa-car'),
('Beauty & Salon','beauty-salon','fa-scissors'),
('Education & Tutors','education-tutors','fa-graduation-cap'),
('Photography','photography','fa-camera'),
('Events','events','fa-calendar-days'),
('Construction','construction','fa-helmet-safety'),
('Tailoring','tailoring','fa-shirt'),
('Fitness','fitness','fa-dumbbell'),
('Other Services','other-services','fa-ellipsis')
ON CONFLICT (slug) DO NOTHING;

INSERT INTO services (category_id, name, slug, description)
SELECT c.id, v.name, v.slug, v.description
FROM (VALUES
('electrical','Electrician','electrician','General electrical installation and repair'),
('electrical','Switchboard Repair','switchboard-repair','Switchboard inspection and repair'),
('plumbing','Plumber','plumber','General plumbing work'),
('plumbing','Leak Repair','leak-repair','Pipe and tap leak repair'),
('carpenter','Carpentry Work','carpentry-work','General carpentry and furniture repair'),
('cleaning','Home Cleaning','home-cleaning','Residential cleaning service'),
('appliance-repair','Washing Machine Repair','washing-machine-repair','Washing machine diagnostics and repair'),
('ac-cooling','AC Repair','ac-repair','Air conditioner diagnostics and repair'),
('ac-cooling','AC Installation','ac-installation','Air conditioner installation'),
('computer-mobile-repair','Computer Repair','computer-repair','Desktop and laptop repair'),
('computer-mobile-repair','Mobile Repair','mobile-repair','Mobile phone diagnostics and repair'),
('automotive','Car Mechanic','car-mechanic','General car repair and maintenance'),
('beauty-salon','Salon Services','salon-services','Beauty and salon services'),
('education-tutors','Home Tutor','home-tutor','Private tutoring services'),
('photography','Event Photography','event-photography','Photography for local events'),
('construction','Masonry Work','masonry-work','Construction and masonry work'),
('tailoring','Tailoring & Alteration','tailoring-alteration','Clothing tailoring and alterations'),
('fitness','Personal Fitness Training','personal-fitness-training','Personal fitness coaching')
) AS v(category_slug,name,slug,description)
JOIN categories c ON c.slug = v.category_slug
ON CONFLICT (category_id, slug) DO NOTHING;

INSERT INTO subscription_plans
(code, name, audience, price_monthly, billing_period_months, tax_rate_bps, tax_label, featured_days, lead_limit, description, is_active)
VALUES
('free','Free','both',0,1,0,'Tax',0,5,'Basic local listing',1),
('professional','Professional','provider',499,1,0,'Tax',7,50,'For independent professionals',1),
('business','Business','business',999,1,0,'Tax',15,NULL,'For local businesses',1)
ON CONFLICT (code) DO NOTHING;
