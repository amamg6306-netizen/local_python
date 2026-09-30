#!/usr/bin/env python3
from pathlib import Path
import re, sys
ROOT=Path(__file__).resolve().parents[2]
passes=[]; fails=[]
def ck(cond,msg):(passes if cond else fails).append(msg)

security=(ROOT/'includes/security.php').read_text()
for needle,msg in [
 ('Content-Security-Policy','CSP header is implemented'),
 ('Strict-Transport-Security','HSTS header is implemented'),
 ("script-src-attr 'none'",'inline script attributes are denied by CSP'),
 ("frame-ancestors 'none'",'framing is denied by CSP'),
 ('csp_nonce()','per-request CSP nonce helper exists'),
]: ck(needle in security,msg)

app=(ROOT/'config/app.php').read_text()
for needle,msg in [
 ('FORCE_HTTPS','production HTTPS enforcement is configurable and required'),
 ('APP_DEBUG must be disabled','production debug-off gate exists'),
 ('APP_ADMIN_MFA_REQUIRED','production admin MFA gate exists'),
 ('UPLOAD_REQUIRE_REENCODE','production upload re-encode gate exists'),
 ('SECURITY_CSP_MODE','production CSP enforcement gate exists'),
 ('TRUSTED_PROXY_IPS','trusted proxy allowlist gate exists'),
]: ck(needle in app,msg)

auth=(ROOT/'includes/auth.php').read_text()
ck("session.use_trans_sid" in auth and "session.use_strict_mode" in auth,'session strict/cookie-only protections are configured')
ck('auth_action_rate_check' in auth and 'auth_action_rate_hit' in auth,'generic recovery-delivery throttling exists')
ck('password_needs_rehash' in (ROOT/'auth/login.php').read_text(),'password hashes are upgraded after successful login')
ck('auth_action_rate_check' in (ROOT/'auth/forgot-password.php').read_text(),'password reset delivery is rate limited')
ck('auth_action_rate_check' in (ROOT/'auth/resend-verification.php').read_text(),'verification resend is rate limited')

# CSP script-src-attr none requires removal of inline JS event attributes.
app_php=[p for p in ROOT.rglob('*.php') if not any(x in p.parts for x in ('tests','tools'))]
event_rx=re.compile(r'\son(?:click|change|submit|load|error|input|focus|blur)\s*=',re.I)
for p in app_php:
    ck(event_rx.search(p.read_text(errors='ignore')) is None,f'{p.relative_to(ROOT)} has no inline JS event-handler attribute')

for p in app_php:
    text=p.read_text(errors='ignore')
    for m in re.finditer(r'<script\b([^>]*)>',text,re.I):
        attrs=m.group(1)
        # Application scripts, including external scripts, must use the request nonce.
        ck('nonce=' in attrs,f'{p.relative_to(ROOT)} script tag uses CSP nonce')

ht=(ROOT/'.htaccess').read_text(); up=(ROOT/'uploads/.htaccess').read_text()
ck('Options -Indexes -MultiViews' in ht and 'Require all denied' in ht,'root web config blocks indexes and sensitive artefacts')
ck('-ExecCGI' in up and 'RemoveHandler .php' in up,'upload directory disables executable handlers')

webhook=(ROOT/'webhooks/razorpay.php').read_text()
ck('enforce_request_body_limit(1048576)' in webhook,'webhook Content-Length is bounded before raw body allocation')
ck('process_razorpay_webhook' in webhook,'webhook still uses signed/idempotent billing processor')

func=(ROOT/'includes/functions.php').read_text()
ck('redact_log_scalar' in func,'security logging has credential-pattern redaction')
ck('error_log' in func and 'json_encode' in func,'security log remains structured and server-side')

mig=(ROOT/'database/production/20260924_005_production_hardening.sql').read_text()
for idx in ['idx_auth_token_expiry','idx_activity_actor_created','idx_checkout_expiry','idx_reconcile_payment_due']:
    ck(idx in mig,f'Phase 6 migration includes {idx}')
ck((ROOT/'database/production/20260924_005_production_hardening_preflight.sql').exists(),'Phase 6 preflight exists')
ck((ROOT/'database/production/20260924_005_production_hardening_rollback.sql').exists(),'Phase 6 rollback exists')

fresh=(ROOT/'database/production/fresh_schema.sql').read_text(errors='ignore')
ck('@localconnect.test' not in fresh.lower(),'production fresh schema has no demo localconnect.test accounts')
ck('DROP TABLE IF EXISTS' not in fresh.upper(),'production fresh schema has no destructive DROP TABLE reset')

env=(ROOT/'.env.example').read_text()
for key in ['FORCE_HTTPS=true','SECURITY_CSP_MODE=enforce','HSTS_MAX_AGE=31536000','PAYMENT_ALLOW_LIVE=false','APP_ADMIN_MFA_REQUIRED=true']:
    ck(key in env,f'.env.example contains safe setting {key}')
ck('REPLACE_WITH_' in env,'environment example contains placeholders rather than real secrets')

least=(ROOT/'database/production/least_privilege_grants.template.sql').read_text()
ck('SELECT, INSERT, UPDATE, DELETE' in least and 'GRANT OPTION' in least,'least-privilege DB template documents web-runtime privileges and prohibited grants')

for rel in ['tools/backup_database.sh','tools/restore_database.sh','tools/secret_scan.py','tools/dependency_inventory.py','tools/release_gate.php','docs/PRODUCTION_DEPLOYMENT_RUNBOOK.md','docs/ROLLBACK_RUNBOOK.md','docs/OWASP_ASVS_5_MAPPING.md']:
    ck((ROOT/rel).exists(),f'{rel} is included')

js=(ROOT/'assets/js/app.js').read_text()
ck('innerHTML' not in js,'favorite UI avoids innerHTML assignment')
ck("LOCALCONNECT_BASE_URL" in js,'AJAX uses configured application base path')

print(f'PASS checks: {len(passes)}')
for x in passes: print('  PASS:',x)
print(f'FAIL checks: {len(fails)}')
for x in fails: print('  FAIL:',x)
sys.exit(1 if fails else 0)
