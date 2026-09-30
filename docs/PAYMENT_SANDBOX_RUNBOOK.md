# LocalConnect Phase 4 — Payment Sandbox Runbook

This runbook is for **Razorpay Test Mode only**. Do not paste live merchant secrets into source files, the database, browser forms, screenshots, tickets or logs.

## 1. Prerequisites

- Production Phase 3 schema is already applied.
- Apply `database/production/20260924_003_checkout_webhooks.sql` after running its preflight.
- PHP must have `pdo_mysql` and `curl` enabled.
- The application must be reachable over HTTPS from Razorpay for real webhook delivery. A localhost-only development server cannot receive internet webhooks without a separately approved secure test exposure.
- An authorized adult business operator must own/configure the merchant sandbox account and credentials.

## 2. Server environment

Configure these only in the process environment or secrets manager:

```text
PAYMENT_RAZORPAY_KEY_ID=<test-mode key id>
PAYMENT_RAZORPAY_KEY_SECRET=<test-mode key secret>
PAYMENT_RAZORPAY_WEBHOOK_SECRET=<test webhook secret>
PAYMENT_ALLOW_LIVE=false
PAYMENT_CHECKOUT_TTL_SECONDS=1800
```

Optionally set `PAYMENT_RAZORPAY_WEBHOOK_IP_ALLOWLIST` to the deployment-approved Razorpay source IP list. HMAC signature verification remains mandatory whether or not an IP list is configured.

Redeploy/restart the Gunicorn web service after changing environment secrets when the platform does not restart it automatically.

## 3. Configure webhook in Razorpay Test Mode

Webhook endpoint:

```text
https://YOUR-HOST/YOUR-BASE-PATH/webhooks/razorpay.php
```

Use the exact same webhook secret that is provided to the application environment. Enable payment capture/failure, refund and dispute-related events required by the merchant's test plan.

The application does not accept a browser session or CSRF token at this endpoint. It authenticates the external request with the Razorpay HMAC signature over the raw body, and optionally the deployment IP allowlist.

## 4. Configure the gateway method in LocalConnect

1. Log in as an administrator.
2. Complete Admin MFA.
3. Re-authenticate with the admin password when prompted.
4. Open **Payment Methods**.
5. Create/edit a Hosted Gateway method with gateway `Razorpay`, audience `Provider`, `Business` or `Both`, currency `INR`.
6. Verify the environment indicators show configured.
7. Enable the method.

No card number, CVV, API secret or webhook secret should ever be entered in this UI.

## 5. Provider test

1. Log in as a provider.
2. Open Provider → Subscription.
3. Select an eligible paid provider plan.
4. Confirm the Payment Method page shows server-generated subtotal/tax/total and only enabled methods.
5. Select Razorpay.
6. Confirm hosted Razorpay Test Checkout opens.
7. Complete a Razorpay-supported test payment using the provider's documented test instruments.
8. Confirm the browser return only says confirmation was received; it must not independently grant entitlement.
9. Deliver/observe the signed `payment.captured` webhook.
10. Confirm Admin → Payment Detail shows the webhook receipt, successful server reconciliation and exactly one linked subscription entitlement.

## 6. Business test

Repeat the flow as a Business account and confirm a provider-only plan cannot be purchased, while a business/both plan can.

## 7. Negative/security tests

- Customer and Admin direct access to billing checkout routes must return/redirect as unauthorized for paid self-checkout.
- Modify `plan_id`, payment method ID or HTML-visible amounts in the browser: the server must reject wrong-role/inactive data and ignore client amount changes.
- Send an invalid webhook HMAC: no payment or subscription state may change.
- Replay the exact same webhook/event key: it must be idempotent.
- Send `payment.failed` after a paid state: it must not downgrade paid entitlement.
- Exercise failed/cancelled/abandoned checkout; if an external order/reference exists the record must remain reconciliation-safe instead of being assumed unpaid.
- Exercise a full refund: linked entitlement must be revoked/cancelled.
- Exercise a partial refund: entitlement remains pending explicit review and payment is flagged for manual review.
- Exercise a dispute event: entitlement must be suspended for review.

## 8. Manual UPI/bank workflow

1. Enable an admin-configured manual UPI or bank method.
2. Provider/business submits a transfer reference.
3. Confirm subscription remains inactive/pending.
4. Admin opens Payment Detail, completes MFA + recent re-authentication, checks the actual merchant account outside LocalConnect and records a review note.
5. Only **Verified paid** may activate entitlement. A fake/reference-only submission must be rejected.

## 9. Reconciliation failures

If gateway API order creation times out or returns an ambiguous server error, Phase 4 sets the payment to `requires_review` and does not automatically create another order. An admin must reconcile the gateway state first. This prevents a blind retry from becoming an accidental double-charge path.

## 10. Live-mode gate

Leave `PAYMENT_ALLOW_LIVE=false` until the final production release gate is satisfied. A live Razorpay key is deliberately rejected while this flag is false.
