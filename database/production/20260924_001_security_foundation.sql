-- LocalConnect production migration 20260924_001
-- Non-destructive security foundation. Back up the DB before applying.
-- Designed for MySQL 8+/MariaDB with InnoDB. No DROP or demo data.
USE localconnect_db;

CREATE TABLE IF NOT EXISTS schema_migrations (
 version VARCHAR(80) PRIMARY KEY,
 applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 checksum_sha256 CHAR(64) NULL
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

CALL lc_add_column_if_missing('users','email_verified_at','DATETIME NULL AFTER last_login_at');
CALL lc_add_column_if_missing('users','session_version','INT UNSIGNED NOT NULL DEFAULT 1 AFTER email_verified_at');
DROP PROCEDURE IF EXISTS lc_add_column_if_missing;

CREATE TABLE IF NOT EXISTS auth_tokens (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 user_id BIGINT UNSIGNED NOT NULL,
 purpose ENUM('password_reset','email_verify') NOT NULL,
 selector CHAR(16) NOT NULL,
 token_hash CHAR(64) NOT NULL,
 expires_at DATETIME NOT NULL,
 used_at DATETIME NULL,
 requested_ip_hash CHAR(64) NULL,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE KEY uq_auth_token_selector(selector),
 INDEX idx_auth_token_user(user_id,purpose,used_at,expires_at),
 CONSTRAINT fk_auth_token_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS auth_rate_limits (
 bucket_hash CHAR(64) PRIMARY KEY,
 attempts INT UNSIGNED NOT NULL DEFAULT 0,
 window_started_at DATETIME NOT NULL,
 blocked_until DATETIME NULL,
 updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 INDEX idx_auth_rate_blocked(blocked_until)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS admin_mfa (
 user_id BIGINT UNSIGNED PRIMARY KEY,
 secret_ciphertext TEXT NOT NULL,
 secret_nonce VARCHAR(128) NOT NULL,
 encryption_alg VARCHAR(40) NOT NULL,
 enabled_at DATETIME NOT NULL,
 last_used_step BIGINT NULL,
 last_verified_at DATETIME NULL,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 CONSTRAINT fk_admin_mfa_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

INSERT IGNORE INTO schema_migrations(version,checksum_sha256) VALUES('20260924_001_security_foundation',NULL);
