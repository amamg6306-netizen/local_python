-- LocalConnect production migration 20260924_004
-- Phase 5: bounded-list supporting indexes and bounded payment reconciliation queue.
-- Forward-only/non-destructive. Run production preflight and take a backup first.
USE localconnect_db;

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
