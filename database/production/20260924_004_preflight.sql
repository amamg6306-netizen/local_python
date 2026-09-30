-- Read-only preflight for Phase 5. Review output before migration.
USE localconnect_db;
SELECT VERSION() AS mysql_version, DATABASE() AS database_name;
SELECT version,applied_at FROM schema_migrations ORDER BY applied_at DESC,version DESC;
SELECT COUNT(*) AS service_requests FROM service_requests;
SELECT COUNT(*) AS reviews FROM reviews;
SELECT COUNT(*) AS failed_webhooks FROM payment_webhook_events WHERE processing_status='failed';
SELECT TABLE_NAME,INDEX_NAME,GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) columns_in_index
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME IN ('service_requests','reviews','favorites','portfolio_images','reports','users')
GROUP BY TABLE_NAME,INDEX_NAME ORDER BY TABLE_NAME,INDEX_NAME;
