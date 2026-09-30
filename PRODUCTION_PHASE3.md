# LocalConnect Production Hardening — Phase 3

Status: **ADMIN PAYMENT-METHOD MANAGEMENT COMPLETE; NOT READY FOR LIVE PAYMENTS**

This phase builds on Production Phase 2. It adds administrator-controlled payment-method configuration while intentionally keeping real checkout, payment capture, webhook-driven entitlement activation, refunds and recurring billing disabled until Phase 4.

## Implemented

- Added `payment_methods` with explicit type (`gateway`, `upi`, `bank_transfer`), role audience, INR currency, display order and active state.
- Added `payment_method_audit` for create/update/activate/deactivate/reorder events.
- Added payment method link/snapshot columns to `payments` so later payment records can preserve the method identity even if an admin disables or renames a method.
- Added Admin → Payment Methods UI for create/edit/enable/disable/reorder.
- Sensitive payment configuration changes require administrator MFA plus a password re-authentication no older than 10 minutes.
- Manual UPI validates a merchant UPI ID and display instructions.
- Manual bank transfer validates beneficiary/reference/instructions.
- Hosted gateway configuration is allowlisted. Phase 3 recognizes Razorpay configuration metadata only; the actual SDK/API checkout is Phase 4.
- Gateway secrets are **not accepted by any browser form and are not stored in LocalConnect database tables**. Admin UI shows only `configured` / `missing` indicators for named environment variables.
- No card number, CVV/CVC or merchant secret field exists in payment-method management.
- No arbitrary external redirect URL field exists for payment methods.

## Disable behavior

Disabling a payment method is deliberately non-destructive:

1. It immediately disappears from `active_payment_methods_for_role()` and therefore is unavailable for **new** checkout selections.
2. Existing `payments` rows are not changed, deleted or auto-failed.
3. Future Phase 4 payment creation will store method code/name/type snapshots. A pending transaction created before a method is disabled remains available for reconciliation or explicit cancellation according to the gateway/manual-payment workflow.
4. Re-enabling a hosted gateway is allowed only after the required environment configuration is complete.

This avoids silently changing the meaning of an in-flight transaction when an administrator changes catalogue configuration.

## Gateway secret configuration and rotation

Use the process environment or deployment secret manager. The expected sandbox variables are documented in `.env.example`:

- `PAYMENT_RAZORPAY_KEY_ID`
- `PAYMENT_RAZORPAY_KEY_SECRET`
- `PAYMENT_RAZORPAY_WEBHOOK_SECRET`

The application only tests whether these values are present; it never returns the values to admin HTML, API output, audit JSON or security logs.

Rotation procedure for Phase 3:

1. Create/rotate the sandbox credential in the payment provider dashboard using an authorized adult business operator account.
2. Update the deployment secret store/process environment, not a web-root file.
3. Restart/reload PHP/Apache/FPM workers so the new environment is loaded.
4. Open Admin → Payment Methods and verify all gateway indicators show `configured`.
5. Do not activate live credentials until Phase 4 signed-webhook and reconciliation tests pass.

A full zero-downtime dual-key rotation strategy is gateway-specific and is deferred to Phase 4, where actual API calls and webhook verification exist.

## Migrations

For an existing Phase 2 production database:

1. Take and verify a backup.
2. Run `database/production/20260924_002_payment_methods_preflight.sql`.
3. Apply `database/production/20260924_002_payment_methods.sql` once.
4. Verify `schema_migrations` contains `20260924_002_payment_methods`.
5. Run application tests before exposing admin payment configuration.

Rollback is provided in `database/production/20260924_002_payment_methods_rollback.sql`. It preserves the base `payments` rows but removes Phase 3 method-link/snapshot columns and all payment-method configuration/audit rows; use only together with an application rollback and verified backup.

## Test evidence

Run:

```bash
tests/phase3/run_phase3.sh
```

The suite includes full PHP syntax lint, payment-helper checks, static sensitive-data/authorization/CSRF controls, and Phase 2 security regression checks.

This audit container does not provide `pdo_mysql`/a MySQL server. Therefore actual migration execution, MFA browser flow and database-backed admin CRUD are **not claimed as runtime-passed here**. Rehearse the migration and admin workflow against a disposable MySQL copy before production.

## Live-payment release gate

**NOT READY FOR LIVE PAYMENTS.** Required later gates include server-created checkout orders/sessions, official provider SDK/API integration, signed webhook verification, replay/idempotency protection, reconciliation, immutable pricing snapshots, entitlement state transitions, refund/dispute behavior, sandbox end-to-end evidence, authorized merchant credentials, independent security review and production smoke testing.
