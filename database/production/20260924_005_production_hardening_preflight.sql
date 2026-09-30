-- LocalConnect Production Phase 6 preflight (read-only)
SELECT DATABASE() AS active_database, VERSION() AS mysql_version;
SELECT version, applied_at FROM schema_migrations ORDER BY applied_at, version;
SELECT COUNT(*) AS active_admins_without_mfa
FROM users u LEFT JOIN admin_mfa m ON m.user_id=u.id
WHERE u.role='admin' AND u.status='active' AND m.user_id IS NULL;
SELECT COUNT(*) AS unverified_active_accounts
FROM users WHERE status='active' AND email_verified_at IS NULL;
SELECT COUNT(*) AS unresolved_payment_reconciliation
FROM payments WHERE reconciliation_status IN ('warning','manual_review') OR status IN ('requires_review','disputed','partially_refunded');
SELECT COUNT(*) AS dead_reconciliation_jobs
FROM payment_reconciliation_jobs WHERE status='dead';
