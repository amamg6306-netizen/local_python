#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
passes=[];fails=[]
def ck(cond,msg):(passes if cond else fails).append(msg)

bounded=[
 'provider/available-requirements.php','provider/requests.php','customer/requests.php',
 'search.php','reviews.php','favorites.php','provider/portfolio.php',
 'admin/users.php','admin/providers.php','admin/businesses.php','admin/reviews.php','admin/reports.php','admin/services.php',
 'provider/services.php','business/services.php','admin/advertisements.php'
]
for rel in bounded:
    s=(ROOT/rel).read_text()
    ck('pagination_window(' in s and 'LIMIT ' in s.upper(),f'{rel} has bounded pagination')
    ck('trim_page_results(' in s,f'{rel} uses per+1 bounded next-page detection')

for rel in ['provider/available-requirements.php','provider/requests.php','customer/requests.php']:
    s=(ROOT/rel).read_text()
    ck('r.*' not in s,f'{rel} avoids broad service_request row fetch')

perf=(ROOT/'includes/performance.php').read_text()
ck("PERF_METRICS_ENABLED" in perf and 'memory_get_peak_usage' in perf and 'duration_ms' in perf,'request duration/peak-memory telemetry available behind opt-in flag')
for forbidden in ['QUERY_STRING','HTTP_COOKIE','user_id','$_GET','$_POST']:
    ck(forbidden not in perf,f'performance log does not capture {forbidden}')
ck('PERF_METRICS_MAX_BYTES' in perf and "performance.log.1" not in perf,'performance log has bounded rotation logic')

func=(ROOT/'includes/functions.php').read_text()
ck('image_decode_fits_memory' in func and 'memory_get_usage(true)' in func,'image decode checks available memory before GD allocation')
ck("imagecreatefromjpeg" in func and "imagecreatefrompng" in func and "imagecreatefromwebp" in func,'image decode streams from temporary file with format-specific decoder')
ck('file_get_contents($tmp)' not in func,'image re-encode no longer copies entire encoded upload into a PHP string')
ck('release_session_lock' in func,'safe session lock release helper exists')
for rel in ['provider/available-requirements.php','provider/requests.php','customer/requests.php','search.php']:
    ck('release_session_lock()' in (ROOT/rel).read_text(),f'{rel} releases session lock on read-heavy path')

mig=(ROOT/'database/production/20260924_004_performance_reliability.sql').read_text()
for idx in ['idx_sr_provider_created','idx_sr_business_created','idx_sr_customer_created','idx_sr_requirement_feed','idx_reviews_customer_created','idx_reviews_target_created']:
    ck(idx in mig,f'performance migration includes {idx}')
ck('payment_reconciliation_jobs' in mig and 'idx_reconcile_due' in mig,'bounded reconciliation queue schema exists')

billing=(ROOT/'includes/billing.php').read_text()
ck('PAYMENT_RECONCILIATION_QUEUE_MAX' in billing,'reconciliation enqueue checks a configured queue cap')
ck('PAYMENT_WORKER_BATCH_MAX' in billing and 'PAYMENT_WORKER_MAX_ATTEMPTS' in billing,'worker batch and retry count are bounded')
ck("status='dead'" in billing and 'next_attempt_at' in billing,'worker has terminal dead state and scheduled retry backoff')
ck('enqueue_payment_reconciliation_job' in billing and 'run_payment_reconciliation_batch' in billing,'failed webhook reconciliation can be queued and processed')
ck('Reconciliation queue is unavailable or full.' in billing,'gateway retry remains fail-safe when recovery queue is unavailable/full')
worker=(ROOT/'tools/payment_reconciliation_worker.php').read_text()
ck("PHP_SAPI !== 'cli'" in worker and 'run_payment_reconciliation_batch' in worker,'reconciliation worker is CLI-only and invokes bounded batch')

env=(ROOT/'.env.example').read_text()
for key in ['PAGINATION_MAX_PAGE','PERF_METRICS_ENABLED','PERF_TARGET_P95_MS','PERF_TARGET_PEAK_MB','PAYMENT_WORKER_BATCH_MAX','PAYMENT_WORKER_MAX_ATTEMPTS','PAYMENT_RECONCILIATION_QUEUE_MAX','PERF_MIN_SAMPLES']:
    ck(key in env,f'.env.example documents {key}')

print(f'PASS checks: {len(passes)}')
for x in passes: print('  PASS:',x)
print(f'FAIL checks: {len(fails)}')
for x in fails: print('  FAIL:',x)
sys.exit(1 if fails else 0)
