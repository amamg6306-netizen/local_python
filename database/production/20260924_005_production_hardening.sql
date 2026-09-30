-- LocalConnect production migration 20260924_005
-- Phase 6 deployment-hardening support indexes only. Non-destructive/idempotent.
-- Back up first and run 20260924_005_production_hardening_preflight.sql.

DELIMITER $$
DROP PROCEDURE IF EXISTS lc_add_index_if_missing$$
CREATE PROCEDURE lc_add_index_if_missing(IN p_table VARCHAR(64), IN p_index VARCHAR(64), IN p_columns TEXT)
BEGIN
 IF NOT EXISTS(
   SELECT 1 FROM information_schema.STATISTICS
   WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=p_table AND INDEX_NAME=p_index
 ) THEN
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
