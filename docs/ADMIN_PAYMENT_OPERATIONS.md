# Admin payment operations

Payment configuration is a privileged operation. Admins must use MFA; payment-method edits and manual reconciliation require recent password re-authentication.

## Payment methods

Create only approved Gateway, Manual UPI or Manual Bank Transfer methods. Gateway secrets are never entered into LocalConnect forms: they come from the server environment/secrets manager. The UI shows configured/missing indicators, not secret values. Manual instructions must be plain text and must not contain card data, passwords, API keys or arbitrary redirect URLs.

Disabling a method blocks new selections but preserves existing pending payment records. Reconcile those records explicitly; do not bulk-mark them cancelled or paid.

## Manual transfers

A payer reference is not proof of payment. Compare the submission with the merchant bank/UPI account through an independently authenticated channel. Approve/reject only after reconciliation; the decision is written to payment history and platform audit logs. Never ask a customer to send a card number/CVV or banking password.

## Gateway incidents

For webhook/signature/API failures, keep the payment pending/reviewable and let the bounded reconciliation worker retry. Do not create another charge just because the browser shows an error. Investigate `requires_review`, failed webhook events and dead reconciliation jobs using provider records plus LocalConnect immutable amount/currency/order snapshots.

## Refunds/disputes

A verified full refund cancels the linked entitlement; a partial refund requires manual entitlement review; a dispute suspends the entitlement pending review. These policies must be reconciled with the merchant agreement and legally reviewed refund terms before live launch.

## Secret rotation

Rotate gateway API/webhook credentials in the provider/secret manager under a planned change. Coordinate webhook-secret changes so delayed provider retries do not get silently accepted with the wrong secret; monitor failed webhooks and reconciliation jobs during the transition. Rotate `APP_KEY` only with a maintenance plan because it protects encrypted admin-MFA seed material and HMAC-derived security buckets; re-enroll/re-encrypt admin MFA before removing the old key. Never paste secrets into tickets, screenshots, Git commits or admin audit notes.
