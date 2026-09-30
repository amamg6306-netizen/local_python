# LocalConnect Performance & Memory Runbook — Production Phase 5

## What Phase 5 changed
High-growth service-request, search, review, favorite, portfolio, provider/business-service and major admin listings now fetch a bounded page (`per_page` is server-clamped) instead of buffering an entire result set. Request feeds select only columns used by the page. Phase 5 also adds supporting indexes, opt-in request timing/peak-memory telemetry, upload decode memory checks, safe session-lock release on read-heavy routes, and a bounded payment reconciliation queue/worker.

This phase does **not** claim that a historical memory leak existed. The Phase 4 code had measurable *unbounded buffering risk*. A leak requires repeatable process-memory growth after requests complete; that was not proven in the build environment.

## Migration rehearsal
1. Back up both database and uploads. Restore that backup on a staging copy and verify it first.
2. Run `database/production/20260924_004_preflight.sql` and save the output.
3. Run `database/production/20260924_004_performance_reliability.sql` during a maintenance window. Index creation can consume I/O and may lock tables depending on your MySQL/MariaDB version and table size.
4. Confirm `schema_migrations` contains `20260924_004_performance_reliability` and run `SHOW INDEX` for `service_requests`, `reviews`, `favorites`, `portfolio_images`, `reports`, and `users`.
5. Do not use the rollback file mechanically. Review queued reconciliation jobs and rehearse rollback on restored data first.

## Representative seeded test data (non-production only)
The seeder refuses `APP_ENV=production`.

```bash
php tools/performance_seed.php --providers=500 --requests=5000
# after testing
php tools/performance_seed.php --cleanup
```

The data is tagged with `@example.invalid` addresses and is removable through cascades. Use larger sizes only on a disposable/staging database with enough disk space.

## Runtime metrics
Set temporarily on staging:

```text
PERF_METRICS_ENABLED=true
PERF_METRICS_MAX_BYTES=10485760
PERF_MIN_SAMPLES=100
PERF_TARGET_P95_MS=750
PERF_TARGET_PEAK_MB=32
```

Telemetry writes JSON lines to `storage/logs/performance.log`, rotates to one backup at the configured size, and contains only timestamp, route path, method, HTTP status, duration, peak PHP memory, and end PHP memory. It does not log query strings, cookies, request bodies, user IDs, card data, or payment secrets.

Summarize and gate it with:

```bash
php tools/performance_log_report.php
php tools/performance_gate.php
```

The default Phase 5 staging gate is at least 100 samples, p95 request latency <= 750 ms, and p95 PHP peak memory <= 32 MiB. These are release-test defaults, not universal production SLOs; establish final targets from the actual production-sized host and traffic model.

## HTTP concurrency probe
Public search example:

```bash
python3 tools/perf_http_probe.py --url "http://localhost/localconnect/search.php?q=repair" --requests 500 --concurrency 10
```

For an authenticated route, copy a short-lived staging session cookie from your own test browser and pass it with `--cookie`. Do not paste production session cookies into reports or source control.

Run at minimum: search, customer requests, provider requests, available requirements, reviews, admin users, and billing history. Record p50/p95/max latency, HTTP status counts, PHP p95 peak memory, DB CPU/slow-query output, and host memory before/after sustained runs.

## Sustained-memory interpretation
A PHP request peak is not proof of a leak. For Apache/FPM workers, capture worker RSS before the run, after warm-up, during sustained traffic, and after idle/recycling. A genuine leak requires reproducible monotonic growth across completed requests that does not return/recycle as expected. If seen, record the smallest reproduction, worker/process identifier, request mix, allocation profile, and before/after RSS. Raising `memory_limit` alone is not a fix.

## Payment/webhook worker bounds
Failed verified webhook processing is queued only for reconciliation; raw webhook bodies are not retained in the queue. Defaults:

```text
PAYMENT_WORKER_BATCH_MAX=20
PAYMENT_WORKER_MAX_ATTEMPTS=5
PAYMENT_RECONCILIATION_QUEUE_MAX=10000
```

Run the worker from a scheduler/CLI only:

```bash
python scripts/payment_reconciliation_worker.py --limit=20
```

Retries use bounded exponential backoff (30 seconds up to 1 hour), stale processing leases are recovered after 10 minutes, and exhausted jobs become `dead` for operator review. When the recovery queue is unavailable/full, a retried failed webhook returns a server failure rather than silently acknowledging recovery.

## Release evidence to retain
Keep the Phase 5 test output, migration/preflight output, `performance_log_report.php` output, `performance_gate.php` output, HTTP probe output, database slow-query/EXPLAIN evidence, worker queue counts, and before/after process-memory measurements. Do not enable live payment traffic until Phase 6 release gates are satisfied.
