-- Phase 4 preflight: read-only checks before applying 20260924_003.
USE localconnect_db;
SELECT VERSION() AS mysql_version;
SELECT version,applied_at FROM schema_migrations ORDER BY applied_at;
SELECT COUNT(*) AS payment_rows FROM payments;
SELECT COUNT(*) AS subscription_rows FROM subscriptions;
SELECT COUNT(*) AS plan_rows FROM subscription_plans;
SELECT COUNT(*) AS active_payment_methods FROM payment_methods WHERE is_active=1;
SELECT provider,provider_order_id,COUNT(*) c FROM payments WHERE provider_order_id IS NOT NULL GROUP BY provider,provider_order_id HAVING c>1;
SELECT provider,provider_payment_id,COUNT(*) c FROM payments WHERE provider_payment_id IS NOT NULL GROUP BY provider,provider_payment_id HAVING c>1;
-- Resolve any duplicate provider IDs before applying the unique indexes.
