USE localconnect_db;
SELECT DATABASE() AS database_name, VERSION() AS server_version;
SELECT COUNT(*) AS admins FROM users WHERE role='admin';
SELECT COUNT(*) AS payments_before FROM payments;
SELECT COUNT(*) AS pending_payments_before FROM payments WHERE status='pending';
SELECT version,applied_at FROM schema_migrations ORDER BY applied_at DESC;
