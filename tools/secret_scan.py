#!/usr/bin/env python3
from pathlib import Path
import re, sys

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {'.git', 'storage', 'uploads', 'tests', 'docs'}
TEXT_EXT = {'.php','.sql','.md','.txt','.json','.js','.css','.py','.sh','.example','.htaccess'}
patterns = [
    (re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'), 'private key material'),
    (re.compile(r'\bAKIA[0-9A-Z]{16}\b'), 'AWS access key'),
    (re.compile(r'\brzp_(?:live|test)_[A-Za-z0-9]{12,}\b'), 'Razorpay key id'),
    (re.compile(r'\bsk_(?:live|test)_[A-Za-z0-9]{12,}\b'), 'payment secret key'),
    (re.compile(r'(?i)PAYMENT_RAZORPAY_KEY_SECRET\s*=\s*(?!REPLACE_WITH_|example|placeholder)([^\s#]{8,})'), 'Razorpay secret assignment'),
    (re.compile(r'(?i)DB_PASS\s*=\s*(?!REPLACE_WITH_|example|placeholder)([^\s#]{8,})'), 'database password assignment'),
    (re.compile(r'(?i)Admin@12345|Customer@123|Provider@123|Business@123'), 'known demo password'),
]

findings=[]
for p in ROOT.rglob('*'):
    if not p.is_file() or any(part in SKIP_DIRS for part in p.parts):
        continue
    if p.resolve() == Path(__file__).resolve():
        continue
    if p.name == '.env.example':
        # Placeholders are expected and intentionally scanned with negative lookaheads above.
        pass
    if p.suffix.lower() not in TEXT_EXT and p.name not in {'.env.example','.htaccess'}:
        continue
    try: text=p.read_text(encoding='utf-8', errors='ignore')
    except Exception: continue
    for rx,label in patterns:
        for m in rx.finditer(text):
            # Test fixtures use deliberately short/example values; regexes above intentionally avoid them.
            line=text.count('\n',0,m.start())+1
            findings.append((str(p.relative_to(ROOT)),line,label))

# Deployable production schema must not seed known test accounts.
fresh=(ROOT/'database/production/fresh_schema.sql').read_text(errors='ignore')
if '@localconnect.test' in fresh.lower(): findings.append(('database/production/fresh_schema.sql',0,'demo account in production schema'))

if findings:
    print(f'FAIL: {len(findings)} possible secret/demo credential finding(s)')
    for f in findings: print(f'  {f[0]}:{f[1]} - {f[2]}')
    sys.exit(1)
print('PASS: no high-confidence embedded production secrets or known demo passwords detected')
