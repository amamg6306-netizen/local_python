#!/usr/bin/env python3
from pathlib import Path
import re, sys
r=Path(__file__).resolve().parents[2]
checks=[]
def c(name, ok, detail=''): checks.append((name,bool(ok),detail))
db=(r/'config/database.php').read_text();app=(r/'config/app.php').read_text();auth=(r/'includes/auth.php').read_text();func=(r/'includes/functions.php').read_text();biz=(r/'business/subscription.php').read_text();sql=(r/'database/localconnect_db.sql').read_text();logout=(r/'auth/logout.php').read_text();
c('production DB no hard-coded root constant', "const DB_USER = 'root'" not in db)
c('production config fail-closed checks', 'production_config_errors' in db and 'DB_PASS' in app)
c('business plan audience fixed', "audience IN ('business','both')" in biz)
c('login throttling implemented', 'login_rate_failure' in auth and 'auth_rate_limits' in (r/'database/production/20260924_001_security_foundation.sql').read_text())
c('session idle+absolute timeout implemented', 'SESSION_IDLE_TIMEOUT' in auth and 'SESSION_ABSOLUTE_TIMEOUT' in auth)
c('logout is POST+CSRF', "REQUEST_METHOD']!=='POST'" in logout and 'verify_csrf()' in logout)
c('MFA secret encrypted', 'encrypt_sensitive' in func and 'secret_ciphertext' in (r/'admin/mfa.php').read_text())
c('password reset token is hashed', "hash('sha256', $validator)" in func)
c('fresh SQL contains no localconnect.test demo users', '@localconnect.test' not in sql)
c('fresh SQL contains no DROP TABLE', 'DROP TABLE' not in sql.upper())
c('upload dimensions/pixels checked', 'UPLOAD_MAX_PIXELS' in func and 'getimagesize' in func)
c('upload path folder allowlist', "['profiles','businesses','portfolio']" in func)
c('production env example has placeholders only', 'REPLACE_WITH_' in (r/'.env.example').read_text() and '@localconnect.test' not in (r/'.env.example').read_text())
# Every browser POST handler must keep CSRF; signed server-to-server webhooks are explicitly exempt.
post=[]; missing=[]
for p in r.rglob('*.php'):
    rel=p.relative_to(r).as_posix()
    if rel.startswith(('tests/','tools/')): continue
    t=p.read_text(errors='ignore')
    if 'REQUEST_METHOD' in t and 'POST' in t:
        post.append(rel)
        if 'verify_csrf()' not in t and 'hash_equals' not in t and 'CSRF_EXEMPT_WEBHOOK' not in t: missing.append(rel)
c('POST CSRF coverage', not missing, f'{len(post)-len(missing)}/{len(post)} handlers; missing={missing}')
for n,ok,d in checks: print(('PASS' if ok else 'FAIL')+': '+n+((' — '+d) if d else ''))
failed=[x for x in checks if not x[1]]
print(f'RESULT: {len(checks)-len(failed)} pass / {len(failed)} fail')
sys.exit(1 if failed else 0)
