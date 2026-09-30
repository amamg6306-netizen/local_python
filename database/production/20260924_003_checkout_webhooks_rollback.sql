-- Phase 4 rollback notes.
-- SAFETY: payment/subscription lifecycle data may have been created after this migration.
-- Do not run on a live database without a verified backup and application rollback.
USE localconnect_db;

DROP TABLE IF EXISTS manual_payment_submissions;
DROP TABLE IF EXISTS payment_webhook_events;
DROP TABLE IF EXISTS payment_status_history;
DROP TABLE IF EXISTS checkout_intents;

-- The added payment/subscription columns are intentionally PRESERVED by default
-- to avoid destroying audit/billing history during rollback. Revert application
-- code first, then remove columns manually only after an audited export.
DELETE FROM schema_migrations WHERE version='20260924_003_checkout_webhooks';
