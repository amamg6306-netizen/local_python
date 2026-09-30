USE localconnect_db;
SELECT DATABASE() AS database_name, VERSION() AS server_version;
SELECT COUNT(*) AS users_before FROM users;
SELECT COUNT(*) AS active_subscriptions_before FROM subscriptions WHERE status='active';
SELECT user_id,COUNT(*) AS active_count FROM subscriptions WHERE status='active' AND (ends_at IS NULL OR ends_at>=NOW()) GROUP BY user_id HAVING COUNT(*)>1;
SELECT COUNT(*) AS demo_named_accounts FROM users WHERE email LIKE '%@localconnect.test';
