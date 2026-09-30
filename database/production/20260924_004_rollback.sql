-- Phase 5 rollback guidance.
-- Application code remains compatible if these performance indexes are removed,
-- but removing indexes can be expensive/locking. Rehearse on a restored backup.
-- Reconciliation jobs should not be dropped while queued/retry/processing rows exist.
USE localconnect_db;
SELECT status,COUNT(*) FROM payment_reconciliation_jobs GROUP BY status;
-- Explicit rollback commands (run only after review):
-- ALTER TABLE service_requests DROP INDEX idx_sr_provider_created, DROP INDEX idx_sr_business_created, DROP INDEX idx_sr_customer_created, DROP INDEX idx_sr_requirement_feed;
-- ALTER TABLE reviews DROP INDEX idx_reviews_customer_created, DROP INDEX idx_reviews_target_created;
-- ALTER TABLE favorites DROP INDEX idx_favorites_customer_created;
-- ALTER TABLE portfolio_images DROP INDEX idx_portfolio_user_created_id;
-- ALTER TABLE reports DROP INDEX idx_reports_created;
-- ALTER TABLE users DROP INDEX idx_users_role_status_id;
-- DROP TABLE payment_reconciliation_jobs;
-- DELETE FROM schema_migrations WHERE version='20260924_004_performance_reliability';
