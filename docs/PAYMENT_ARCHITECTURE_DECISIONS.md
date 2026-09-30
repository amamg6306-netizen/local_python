# Payment Architecture / Security Decisions — Phase 4

## Trust boundaries

- Browser: untrusted for plan price, status, role, payment success and payment method activation.
- LocalConnect server: authoritative for authenticated user, role, plan eligibility, immutable price snapshot and entitlement state.
- Razorpay: authoritative external source for gateway order/payment status, but webhook authenticity must be verified and payment/order data must be reconciled to the LocalConnect snapshot.
- Admin manual reconciliation: authoritative only after MFA + recent password re-authentication and external merchant-account verification.

## Card-data scope

LocalConnect does not render fields for PAN/card number or CVV/CVC and does not accept those values in application endpoints. Razorpay hosted Checkout is responsible for collection of supported payment instrument details. The application stores only gateway references and its own billing metadata.

## Price integrity

The browser submits only a plan identifier when checkout starts. The server loads the active role-appropriate plan and stores subtotal/tax/total/billing-period snapshots in `checkout_intents` and `payments`. Gateway orders use the stored payment amount, converted to currency subunits server-side.

## Webhook/idempotency

- Signature = HMAC over exact raw webhook body using the environment-only webhook secret.
- `payment_webhook_events(provider,event_key)` is unique.
- Provider order/payment identifiers are unique per provider.
- Raw webhook payloads are not persisted; only event metadata and a SHA-256 payload hash are retained.
- Entitlement creation locks the payment row and links `subscriptions.source_payment_id` uniquely.

## State policy

- `paid`: only after manual external reconciliation or signed webhook + server API reconciliation.
- `failed`: no entitlement; a later verified capture can still recover the state.
- `cancelled`: only authoritative when no external payment reference/submission existed.
- external reference exists + user stops checkout: `requires_review`, not assumed cancelled.
- `refunded`: full refund revokes linked entitlement.
- `partially_refunded`: entitlement retained but payment marked manual review.
- `disputed`: entitlement suspended pending review.

## Gateway outage policy

Definitive gateway 4xx order rejection may fail the attempt. Transport failure or gateway 5xx is treated as ambiguous; automatic retry is suppressed and reconciliation is required.

## Recurring billing

Automatic recurring charging is intentionally not implemented. Current paid plans are fixed-period prepaid entitlements. Future recurring billing must use the payment provider's approved recurring/subscription product and its webhook state model rather than reusing one-time order assumptions.
