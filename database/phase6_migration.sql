USE localconnect_db;
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
ALTER TABLE advertisements ADD COLUMN IF NOT EXISTS sponsor_user_id BIGINT UNSIGNED NULL AFTER created_by, ADD COLUMN IF NOT EXISTS budget DECIMAL(10,2) NOT NULL DEFAULT 0 AFTER placement, ADD COLUMN IF NOT EXISTS impressions INT UNSIGNED NOT NULL DEFAULT 0 AFTER budget, ADD COLUMN IF NOT EXISTS clicks INT UNSIGNED NOT NULL DEFAULT 0 AFTER impressions;
