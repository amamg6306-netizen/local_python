-- CAUTION: rollback removes Phase 3 payment-method configuration and audit history.
-- Existing payment records are preserved, but their Phase 3 method-link/snapshot columns are removed.
-- Take a verified backup first and roll application code back atomically.
USE localconnect_db;
ALTER TABLE payments DROP FOREIGN KEY fk_payment_method;
ALTER TABLE payments DROP INDEX idx_payment_method;
ALTER TABLE payments DROP COLUMN payment_method_type_snapshot;
ALTER TABLE payments DROP COLUMN payment_method_name_snapshot;
ALTER TABLE payments DROP COLUMN payment_method_code_snapshot;
ALTER TABLE payments DROP COLUMN payment_method_id;
DROP TABLE IF EXISTS payment_method_audit;
DROP TABLE IF EXISTS payment_methods;
DELETE FROM schema_migrations WHERE version='20260924_002_payment_methods';
