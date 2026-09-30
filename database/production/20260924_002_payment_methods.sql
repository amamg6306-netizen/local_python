-- LocalConnect production migration 20260924_002
-- Admin-managed payment methods. Non-destructive forward migration.
-- Back up the database and run the matching preflight first.
USE localconnect_db;

CREATE TABLE IF NOT EXISTS payment_methods (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 code VARCHAR(60) NOT NULL UNIQUE,
 name VARCHAR(120) NOT NULL,
 method_type ENUM('gateway','upi','bank_transfer') NOT NULL,
 gateway_code VARCHAR(60) NULL,
 audience ENUM('provider','business','both') NOT NULL DEFAULT 'both',
 currency CHAR(3) NOT NULL DEFAULT 'INR',
 merchant_upi_id VARCHAR(190) NULL,
 bank_beneficiary VARCHAR(160) NULL,
 bank_reference VARCHAR(190) NULL,
 display_instructions VARCHAR(2000) NULL,
 display_order INT UNSIGNED NOT NULL DEFAULT 100,
 is_active TINYINT(1) NOT NULL DEFAULT 0,
 created_by BIGINT UNSIGNED NOT NULL,
 updated_by BIGINT UNSIGNED NOT NULL,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 CONSTRAINT fk_payment_method_created_by FOREIGN KEY(created_by) REFERENCES users(id) ON DELETE RESTRICT,
 CONSTRAINT fk_payment_method_updated_by FOREIGN KEY(updated_by) REFERENCES users(id) ON DELETE RESTRICT,
 INDEX idx_payment_method_active(audience,currency,is_active,display_order),
 INDEX idx_payment_method_type(method_type,gateway_code)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS payment_method_audit (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 payment_method_id BIGINT UNSIGNED NOT NULL,
 admin_user_id BIGINT UNSIGNED NOT NULL,
 action VARCHAR(40) NOT NULL,
 before_json JSON NULL,
 after_json JSON NULL,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT fk_pma_method FOREIGN KEY(payment_method_id) REFERENCES payment_methods(id) ON DELETE RESTRICT,
 CONSTRAINT fk_pma_admin FOREIGN KEY(admin_user_id) REFERENCES users(id) ON DELETE RESTRICT,
 INDEX idx_pma_method(payment_method_id,created_at),
 INDEX idx_pma_admin(admin_user_id,created_at)
) ENGINE=InnoDB;

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

CALL lc_add_column_if_missing('payments','payment_method_id','BIGINT UNSIGNED NULL AFTER subscription_id');
CALL lc_add_column_if_missing('payments','payment_method_code_snapshot','VARCHAR(60) NULL AFTER payment_method_id');
CALL lc_add_column_if_missing('payments','payment_method_name_snapshot','VARCHAR(120) NULL AFTER payment_method_code_snapshot');
CALL lc_add_column_if_missing('payments','payment_method_type_snapshot','VARCHAR(40) NULL AFTER payment_method_name_snapshot');
DROP PROCEDURE IF EXISTS lc_add_column_if_missing;

DELIMITER $$
DROP PROCEDURE IF EXISTS lc_add_fk_if_missing$$
CREATE PROCEDURE lc_add_fk_if_missing()
BEGIN
 IF NOT EXISTS(
  SELECT 1 FROM information_schema.TABLE_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA=DATABASE() AND TABLE_NAME='payments' AND CONSTRAINT_NAME='fk_payment_method'
 ) THEN
  ALTER TABLE payments ADD CONSTRAINT fk_payment_method FOREIGN KEY(payment_method_id) REFERENCES payment_methods(id) ON DELETE SET NULL;
 END IF;
 IF NOT EXISTS(
  SELECT 1 FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='payments' AND INDEX_NAME='idx_payment_method'
 ) THEN
  ALTER TABLE payments ADD INDEX idx_payment_method(payment_method_id,status,created_at);
 END IF;
END$$
DELIMITER ;
CALL lc_add_fk_if_missing();
DROP PROCEDURE IF EXISTS lc_add_fk_if_missing;

INSERT IGNORE INTO schema_migrations(version,checksum_sha256) VALUES('20260924_002_payment_methods',NULL);
