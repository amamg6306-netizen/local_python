# LocalConnect Production Phase 6 — test report

## Build runner

- PHP CLI: 8.4.23
- Available relevant extensions: base `PDO`, Fileinfo, OpenSSL, Sodium
- Unavailable in this runner: `pdo_mysql`, GD, PHP cURL, MySQL/MariaDB service
- No public HTTPS staging URL or authorized Razorpay sandbox credentials/webhook endpoint were available

Those limitations are treated as release blockers. No unavailable database/browser/payment/load test is reported as passed.

## Executed automated suite

Command:

```bash
tests/phase6/run_phase6.sh
```

Executed results:

- PHP syntax lint: **93 PHP files PASS**
- Phase 6 PHP security helper checks: **8 PASS / 0 FAIL**
- Phase 6 static production-hardening checks: **133 PASS / 0 FAIL**
- high-confidence embedded secret/demo credential scan: **PASS**
- external dependency/resource inventory checks: **4 PASS / 0 FAIL**
- deployment shell syntax: **PASS**
- real HTTPS security-header probe: **SKIPPED** because `PHASE6_BASE_URL` was not available
- Phase 5 performance/reliability static checks: **71 PASS / 0 FAIL**
- Phase 5 memory buffering proxy: **PASS**
- Phase 4 billing helper regression: **11 PASS / 0 FAIL**
- Phase 4 checkout/webhook static regression: **37 PASS / 0 FAIL**
- Phase 3 payment helper regression: **11 PASS / 0 FAIL**
- Phase 3 payment-method static regression: **21 PASS / 0 FAIL**
- Phase 2 helper/static regression: **14 PASS / 0 FAIL**
- Phase 1 baseline scanner: **9 PASS / 0 WARN / 0 FAIL**
- detected state-changing POST handlers in the regression scanner: **37/37 CSRF coverage**
- packaged release gate fail-safe check: **PASS**; expected status is `NOT_READY_FOR_LIVE_PAYMENTS`

## Memory evidence retained from Phase 5

The reproducible PHP buffering proxy remains:

```text
Unbounded proxy: 20,000 representative request rows -> peak 35,651,584 bytes (~34.0 MiB)
Bounded proxy:        25 representative request rows -> peak  2,097,152 bytes (2.0 MiB)
Peak-memory ratio: 17.0x
```

This demonstrates bounded result buffering in the fixture only. It is **not** evidence of a process memory leak or a substitute for Apache/FPM RSS profiling with MySQL-backed traffic.

## Tests still mandatory on staging/production

1. Apply Phase 1-6 migrations to a restored MySQL/MariaDB clone; run every preflight and rehearse rollback.
2. Full customer/provider/business/admin authorization and IDOR browser matrix with real database state.
3. HTTPS header/CSP test in a real browser, including Razorpay hosted checkout compatibility.
4. Password reset and email verification through the configured production mail transport.
5. Valid/invalid/oversized image decode and re-encode tests using production GD and memory limits.
6. Razorpay Test Mode end-to-end: provider Professional and business Business, signed webhook, exact-once entitlement, invalid/duplicate/replayed events, failure/cancellation/refund/dispute and manual payment review.
7. Representative data/load test, DB `EXPLAIN` evidence, p50/p95 latency, PHP peak memory and sustained Apache/FPM RSS. Default code-level target: >=100 healthy samples, p95 <=750 ms and p95 PHP peak <=32 MiB; production target must be approved for the actual host.
8. Reconciliation worker outage/retry/dead-queue behavior against Test Mode API/webhooks.
9. Backup creation, checksum, isolated restore and application verification.
10. Independent security review/penetration test, legal/tax/refund review and final production smoke test.

## Current release gate output

The packaged environment reports **NOT_READY_FOR_LIVE_PAYMENTS** because it is not production-configured, `pdo_mysql`/GD/cURL are unavailable, mail is not configured here, and the required external evidence files are intentionally absent. `PAYMENT_ALLOW_LIVE=false` is intentionally retained as the safe pre-live setting and is not itself a blocker.

This is the expected fail-safe status. Do not create fake evidence or enable live charging to make the gate pass.
