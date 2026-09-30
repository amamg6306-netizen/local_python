-- LocalConnect Phase 6 rollback: drops only Phase 6 support indexes/marker.
-- Application hardening code should be rolled back together with this DB change if needed.
DELIMITER $$
DROP PROCEDURE IF EXISTS lc_drop_index_if_exists$$
CREATE PROCEDURE lc_drop_index_if_exists(IN p_table VARCHAR(64), IN p_index VARCHAR(64))
BEGIN
 IF EXISTS(
   SELECT 1 FROM information_schema.STATISTICS
   WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=p_table AND INDEX_NAME=p_index
 ) THEN
   SET @sql=CONCAT('ALTER TABLE `',p_table,'` DROP INDEX `',p_index,'`');
   PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
 END IF;
END$$
DELIMITER ;

CALL lc_drop_index_if_exists('auth_tokens','idx_auth_token_expiry');
CALL lc_drop_index_if_exists('platform_activity','idx_activity_actor_created');
CALL lc_drop_index_if_exists('checkout_intents','idx_checkout_expiry');
CALL lc_drop_index_if_exists('payment_reconciliation_jobs','idx_reconcile_payment_due');
DROP PROCEDURE IF EXISTS lc_drop_index_if_exists;
DELETE FROM schema_migrations WHERE version='20260924_005_production_hardening';
