# LocalConnect Production Hardening — Phase 4

Status: **SANDBOX CHECKOUT + WEBHOOK/RECONCILIATION CODE COMPLETE; NOT READY FOR LIVE PAYMENTS**

This cumulative phase builds on Production Phase 3 and adds provider/business subscription checkout without trusting client-side price or browser-return status.

## What changed

- Provider and Business subscription pages now show role-appropriate active plans, billing period, subtotal, configured tax line, total, benefits and current plan state.
- `Get Subscription` creates a short-lived server-side checkout intent with a random token whose database value is stored only as a SHA-256 hash.
- Plan role/audience and plan activity are re-validated server-side. Client-supplied amounts are never accepted.
- Payment Method page shows only active, correctly scoped and fully configured admin-managed methods.
- Hosted gateway integration supports Razorpay Test Mode via the official Orders/Payments API and Razorpay Checkout.
- Razorpay Key Secret and Webhook Secret remain server environment/secrets-manager values. The browser receives only the public Key ID and gateway order ID needed by hosted Checkout.
- Browser callback signatures are verified but **never mark a payment paid and never activate entitlement**.
- Signed Razorpay webhooks are verified over the exact raw body, deduplicated, stored without the raw payload, and reconciled by fetching both the payment and order from Razorpay before paid state is accepted.
- External order/payment IDs and webhook event keys have database uniqueness constraints for idempotency/replay protection.
- Gateway transport/5xx ambiguity moves the payment to `requires_review`; the app does not blindly retry a potentially-created remote order.
- `payment.failed` cannot overwrite an already paid/refunded/disputed payment. A later verified capture can recover a previously failed local state.
- Refund handling distinguishes partial from full refund. Full refund revokes the linked entitlement; partial refund keeps entitlement pending explicit review.
- Dispute events set payment to `disputed` and suspend the linked entitlement pending administrator review.
- Manual UPI/bank transfers create pending payment records. A payer reference is not proof. Only an MFA + recent-password reauthenticated administrator can verify/reject after checking the external merchant account.
- Checkout abandonment after an external order/reference exists is not assumed to mean “no charge”; it moves to reconciliation review.
- Paid payment activation is transactionally linked to one subscription entitlement through `source_payment_id`. Replayed/concurrent success processing returns the existing entitlement rather than creating a second one.
- Admin Payments and Subscriptions are filtered and paginated; Payment Detail includes status history, webhook receipt metadata and reconciliation controls.

## Pricing/tax policy

`subscription_plans.tax_rate_bps` defaults to `0`. Phase 4 does not assume a GST/tax rate. The authorized business operator must set the legally reviewed rate/label for the applicable market before collecting live payments.

## Recurring policy

This phase implements fixed-period prepaid entitlements, not automatic recurring debits. A plan period defaults to one month and a new verified checkout is required for a renewal. The database/state model supports scheduled entitlements, but Razorpay Subscriptions/UPI AutoPay is not enabled in this phase.

## Versioned migration

For an existing Production Phase 3 database:

1. Take and verify a backup.
2. Run `database/production/20260924_003_checkout_webhooks_preflight.sql`.
3. Resolve any duplicate external payment/order identifiers reported by the preflight.
4. Apply `database/production/20260924_003_checkout_webhooks.sql` once.
5. Verify `schema_migrations` includes `20260924_003_checkout_webhooks`.
6. Run `tests/phase4/run_phase4.sh` and then the sandbox browser flow in `docs/PAYMENT_SANDBOX_RUNBOOK.md`.

Rollback notes are in `database/production/20260924_003_checkout_webhooks_rollback.sql`. The rollback intentionally preserves added billing columns because deleting real billing history is not a safe default.

## Release gate

**NOT READY FOR LIVE PAYMENTS.** Live credentials are blocked by default with `PAYMENT_ALLOW_LIVE=false`.

Before live enablement, all of the following still need independent evidence: successful MySQL migration rehearsal, Razorpay Test Mode end-to-end payment + signed webhook, failure/refund/dispute tests, authorized merchant account configuration by an adult business operator, legal/tax/refund review, Phase 5 performance work, Phase 6 production hardening, independent security review/penetration test and a production smoke test.
