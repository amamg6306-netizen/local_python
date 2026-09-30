USE localconnect_db;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS resolution_note VARCHAR(500) NULL AFTER resolved_by;
CREATE TABLE IF NOT EXISTS platform_activity (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, actor_id BIGINT UNSIGNED NULL, action VARCHAR(100) NOT NULL, target_type VARCHAR(60) NULL, target_id BIGINT UNSIGNED NULL, details VARCHAR(500) NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT fk_activity_actor FOREIGN KEY(actor_id) REFERENCES users(id) ON DELETE SET NULL, INDEX idx_activity_created(created_at), INDEX idx_activity_action(action)
) ENGINE=InnoDB;
