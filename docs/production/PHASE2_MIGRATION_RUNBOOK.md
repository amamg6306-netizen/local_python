# Phase 2 migration runbook

1. Back up the database and verify restore on a disposable database. For a brand-new empty production database, use `database/production/fresh_schema.sql` against a database created by your DBA/host; it contains no demo accounts and no DROP statements.
2. Run `database/production/20260924_001_security_foundation_preflight.sql`; investigate duplicate active subscriptions and any `@localconnect.test` accounts before proceeding.
3. Put the application in a maintenance window for the migration rehearsal/production cutover.
4. Apply `database/production/20260924_001_security_foundation.sql` once. It adds columns/tables and does not drop marketplace data.
5. Configure production environment values from `.env.example` through the web server/process environment or a secrets manager. Do not put real secrets inside the public document root.
6. Run `php tools/check_production_config.php` with `APP_ENV=production`.
7. Create the first production admin only if needed using `LOCALCONNECT_ADMIN_NAME`, `LOCALCONNECT_ADMIN_EMAIL`, and `LOCALCONNECT_ADMIN_PASSWORD` with `php tools/create_admin.php`; remove those temporary environment values immediately afterward.
8. Login as admin and enable MFA at `/admin/mfa.php` before privileged operation.
9. Execute `./tests/phase2/run_phase2.sh`, then run the DB/browser regression matrix from Phase 1 against the migrated clone.
10. Roll back application + DB together only if necessary. The rollback SQL deletes Phase 2 authentication/MFA state, so take another backup before running it.

The production-hardening artifact contains no built-in demo credentials or destructive demo-reset SQL. Create disposable local test users explicitly; never copy production data into development.
