-- CAUTION: rollback deletes Phase 2 security-token/MFA/rate-limit state.
-- Take a backup first. Application code must also be rolled back atomically.
USE localconnect_db;
DROP TABLE IF EXISTS admin_mfa;
DROP TABLE IF EXISTS auth_rate_limits;
DROP TABLE IF EXISTS auth_tokens;
ALTER TABLE users DROP COLUMN session_version;
ALTER TABLE users DROP COLUMN email_verified_at;
DELETE FROM schema_migrations WHERE version='20260924_001_security_foundation';
