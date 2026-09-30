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
