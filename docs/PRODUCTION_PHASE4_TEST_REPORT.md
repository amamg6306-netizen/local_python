# LocalConnect Production Phase 4 — Test Report

Status: **CODE GATES PASS; SANDBOX E2E NOT EXECUTED; NOT READY FOR LIVE PAYMENTS**

## Environment

Audit container findings:

- PHP CLI available.
- `PDO` core available.
- `pdo_mysql`, MySQL/MariaDB server/client, PHP cURL and GD were **not available** in this container.
- Therefore MySQL migration execution, browser/database checkout, outbound Razorpay API calls and real Razorpay webhook delivery were not executed here.

This limitation is intentionally not converted into a success claim.

## Commands executed

```bash
./tests/phase4/run_phase4.sh
```

The suite performs:

1. PHP syntax lint across the full tree.
2. Phase 4 money/signature/live-key guard helper tests.
3. Phase 4 checkout/webhook static security tests.
4. Phase 3 payment-method regression tests.
5. Phase 2 security regression tests.
6. Baseline security scanner.

A separate source scan checked for LocalConnect card/CVV input fields and obvious committed live Razorpay secret assignments.

## Results

- PHP lint: **84/84 PHP files PASS**.
- Phase 4 helper tests: **11 PASS / 0 FAIL**.
- Phase 4 checkout/webhook controls: **37 PASS / 0 FAIL**.
- Phase 3 helper regression: **11 PASS / 0 FAIL**.
- Phase 3 static payment-method regression: **21 PASS / 0 FAIL**.
- Phase 2 helper regression: **7 PASS / 0 FAIL**.
- Phase 2 static security regression: **14 PASS / 0 FAIL**.
- Baseline scanner: **9 PASS / 0 FAIL / 5 known WARN**.
- Browser POST CSRF coverage in the Phase 2 scanner: **37/37 detected browser handlers covered**; the Razorpay webhook is explicitly server-to-server and authenticated by HMAC instead of CSRF.
- Source scan: **0 detected LocalConnect card/CVV form fields; 0 obvious committed live Razorpay secret assignments**.

## Known baseline warnings retained for later phases

1. Application HSTS is not yet emitted — Phase 6 production hardening.
2. CSP is not yet emitted — Phase 6 production hardening, after accounting for actual CDN/hosted-checkout assets.
3. `provider/available-requirements.php` has unbounded `fetchAll()` — Phase 5 performance/memory work.
4. `provider/requests.php` has unbounded `fetchAll()` — Phase 5.
5. `customer/requests.php` has unbounded `fetchAll()` — Phase 5.

These are not described as confirmed memory leaks because no sustained profiling has been run yet.

## Phase 4 acceptance coverage from static/unit tests

PASS evidence exists for:

- Provider/business-only paid checkout route guards.
- Correct provider/business plan audience filtering.
- Server-side plan validation and immutable pricing snapshots.
- No client-supplied payment amount trust.
- Only active, role-appropriate, configured methods selectable.
- Hosted Razorpay Checkout integration; no LocalConnect PAN/CVV inputs.
- Browser callback cannot mark `paid` or activate entitlement.
- Raw-body webhook HMAC verification.
- Webhook replay/idempotency constraint.
- Unique provider order/payment identifiers.
- Server-side fetch/reconciliation of Razorpay payment and order before activation.
- Ambiguous gateway failure -> review, not blind automatic retry.
- Manual transfer remains pending until MFA/re-authenticated admin review.
- Full vs partial refund policy.
- Dispute -> suspended entitlement/manual review.
- Live credentials disabled by default with `PAYMENT_ALLOW_LIVE=false`.
- User/admin billing ledgers paginated.

## Tests still required on a real sandbox stack

The following must be executed before this phase can be called sandbox-E2E verified:

- Apply preflight + migration on a disposable MySQL copy and validate schema/FKs/indexes.
- Provider -> Professional plan -> enabled Razorpay Test Mode method -> hosted checkout -> signed `payment.captured` webhook -> exactly one entitlement.
- Business -> Business plan with same flow.
- Customer/Admin direct paid self-checkout denial.
- Browser plan/method/price tampering.
- Invalid signature, duplicate webhook and delayed/out-of-order events.
- Gateway timeout/5xx reconciliation path.
- Failed payment after paid state.
- Full refund, partial refund and dispute state changes.
- Manual UPI/bank pending -> admin verification/rejection.
- Disabled payment method while a transaction is pending.
- Secret/log response inspection on the deployed web server.

Use `docs/PAYMENT_SANDBOX_RUNBOOK.md` for the reproducible procedure.

## Release gate

**NOT READY FOR LIVE PAYMENTS.**

Exact blockers:

- No authorized Razorpay sandbox credentials were supplied to this environment.
- No reachable HTTPS webhook test endpoint was available.
- No MySQL/PDO-MySQL runtime was available for migration/browser integration tests.
- Phase 5 performance/memory work is not complete.
- Phase 6 production hardening/deployment rehearsal is not complete.
- Independent security review/penetration test is not complete.
- Legal/tax/refund-policy review for the target business/market is not complete.
- Authorized adult business operator has not completed live merchant configuration in this environment.
