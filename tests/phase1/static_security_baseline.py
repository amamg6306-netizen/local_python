#!/usr/bin/env python3
from pathlib import Path
import re, sys

ROOT = Path(__file__).resolve().parents[2]
php_files = [p for p in ROOT.rglob('*.php') if '/tests/' not in p.as_posix() and '/tools/' not in p.as_posix()]
passes=[]; warnings=[]; failures=[]

def ok(cond, msg):
    (passes if cond else failures).append(msg)

def warn(cond, msg):
    if cond: warnings.append(msg)

# POST/CSRF coverage (manual AJAX hash_equals is accepted)
post_files=[]
for p in php_files:
    s=p.read_text(encoding='utf-8', errors='ignore')
    if "REQUEST_METHOD']==='POST'" in s or "REQUEST_METHOD'] === 'POST'" in s or 'REQUEST_METHOD"] === "POST"' in s:
        post_files.append(p)
        csrf = 'verify_csrf()' in s or ('csrf_token' in s and 'hash_equals' in s) or 'CSRF_EXEMPT_WEBHOOK' in s
        if not csrf:
            failures.append(f'{p.relative_to(ROOT)}: POST handler without detected CSRF validation')
ok(len(post_files) > 0, f'detected {len(post_files)} POST handlers')
if not any('POST handler without' in x for x in failures):
    passes.append(f'all {len(post_files)} detected POST handlers have CSRF validation')

login=(ROOT/'auth/login.php').read_text()
register=(ROOT/'auth/register.php').read_text()
db=(ROOT/'config/database.php').read_text()
appcfg=(ROOT/'config/app.php').read_text() if (ROOT/'config/app.php').exists() else ''
auth=(ROOT/'includes/auth.php').read_text()
func=(ROOT/'includes/functions.php').read_text()
bs=(ROOT/'business/subscription.php').read_text()
prov=(ROOT/'provider/subscription.php').read_text()
sql=(ROOT/'database/localconnect_db.sql').read_text()

ok('password_verify(' in login, 'login uses password_verify')
ok('session_regenerate_id(true)' in login, 'login rotates the session id')
ok('password_hash(' in register, 'registration uses password_hash')
ok('PDO::ATTR_EMULATE_PREPARES => false' in db, 'PDO emulated prepares are disabled')
ok('httponly' in auth and 'samesite' in auth, 'session cookie has HttpOnly and SameSite settings')
ok('finfo(FILEINFO_MIME_TYPE)' in func and 'random_bytes(16)' in func, 'uploads use MIME inspection and random server filenames')
ok("audience IN ('provider','both')" in prov, 'provider plan audience filter is provider/both')

# Known baseline warnings expected to be fixed in later phases.
warn("const DB_USER = 'root'" in db and "const DB_PASS = ''" in db, 'production DB configuration is hard-coded to root with blank password')
warn('getenv(' not in db+appcfg and '$_ENV' not in db+appcfg and 'env_value(' not in db+appcfg, 'database configuration is not environment/secrets based')
warn("audience IN ('provider','both')" in bs, "business subscription incorrectly queries provider/both plans")
warn(('billing/start.php' not in prov and 'billing/start.php' not in bs), 'subscription purchase buttons are disabled; no checkout exists')
warn('webhook' not in ''.join(p.read_text(errors='ignore').lower() for p in php_files), 'no payment webhook implementation detected')
warn('@localconnect.test' in sql and 'DEMO' in sql, 'demo admin credentials/data exist in the deployable SQL seed')
warn('DROP TABLE IF EXISTS' in sql, 'fresh SQL is destructive and unsuitable as a production migration')
warn(not any(term in login.lower() for term in ['login_attempt','failed_attempt','throttle','rate_limit','retry_after']), 'login throttling is not implemented')
all_php=''.join(p.read_text(errors='ignore').lower() for p in php_files)
warn('mfa' not in all_php and 'totp' not in all_php, 'admin MFA is not implemented')
warn('forgot' not in all_php and 'reset_token' not in all_php, 'password reset flow is not implemented')
warn('email_verified' not in all_php and 'verification_token' not in all_php, 'email verification flow is not implemented')
warn('getimagesize' not in func and 'imagecreatefrom' not in func, 'upload validation does not decode/inspect image dimensions or pixel count')
security_headers=((ROOT/'includes/header.php').read_text() + ((ROOT/'includes/security.php').read_text() if (ROOT/'includes/security.php').exists() else ''))
warn('Strict-Transport-Security' not in security_headers, 'HSTS is not emitted by the application')
warn('Content-Security-Policy' not in security_headers, 'CSP is not emitted by the application')
warn((ROOT/'auth/logout.php').exists() and "REQUEST_METHOD" not in (ROOT/'auth/logout.php').read_text(), 'logout is a GET-triggered state change with no CSRF requirement')

# Unbounded fetchAll candidates.
for rel in ['provider/available-requirements.php','provider/requests.php','customer/requests.php']:
    s=(ROOT/rel).read_text()
    if 'fetchAll()' in s and 'LIMIT ' not in s.upper():
        warnings.append(f'{rel} performs an unbounded fetchAll()')

# Subscription concurrency warning.
if 'INSERT INTO subscriptions' in func and 'FOR UPDATE' not in func and 'INSERT IGNORE' not in func:
    warnings.append('ensure_free_subscription() has no locking/unique active-subscription guard; concurrent calls can create duplicates')

print(f'PASS checks: {len(passes)}')
for x in passes: print('  PASS:', x)
print(f'WARN findings: {len(warnings)}')
for x in warnings: print('  WARN:', x)
print(f'FAIL checks: {len(failures)}')
for x in failures: print('  FAIL:', x)
if failures:
    sys.exit(1)
