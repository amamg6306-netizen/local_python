# Production Hardening Phase 2

This cumulative build starts from Production Phase 1 and implements the security/migration foundation for the later payment work.

Key documents:

- `docs/production/PHASE2_SECURITY_IMPLEMENTATION.md`
- `docs/production/PHASE2_MIGRATION_RUNBOOK.md`
- `docs/production/PHASE2_AUTH_OPERATIONS.md`
- `docs/production/PHASE2_ROUTE_SECURITY_AUDIT.md`
- `docs/production/PHASE2_TEST_REPORT.md`

Apply `database/production/20260924_001_security_foundation.sql` only after backup and preflight on an existing database. For a brand-new empty production database, use `database/production/fresh_schema.sql` against a database pre-created by the operator/host.

**Release status: NOT READY FOR LIVE PAYMENTS.**
