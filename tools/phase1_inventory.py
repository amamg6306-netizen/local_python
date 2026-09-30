#!/usr/bin/env python3
from pathlib import Path
import csv, re, hashlib
ROOT = Path(__file__).resolve().parents[1]
PHP = sorted(ROOT.rglob('*.php'))
EXCLUDE_PREFIXES = ('tests/', 'tools/')
rows=[]
for p in PHP:
    rel=p.relative_to(ROOT).as_posix()
    if rel.startswith(EXCLUDE_PREFIXES):
        continue
    s=p.read_text(encoding='utf-8', errors='ignore')
    post="REQUEST_METHOD']==='POST'" in s or 'REQUEST_METHOD"] === "POST"' in s or "REQUEST_METHOD'] === 'POST'" in s
    csrf='verify_csrf()' in s or ('csrf_token' in s and 'hash_equals' in s)
    m=re.search(r"require_role\(([^)]*)\)", s)
    auth='public'
    if m:
        auth='role:'+re.sub(r'\s+',' ',m.group(1)).strip()
    elif 'require_login()' in s:
        auth='login'
    elif 'require_guest()' in s:
        auth='guest-only'
    elif rel=='ajax/favorite.php':
        auth='customer (manual)'
    if rel=='business/requests.php':
        auth='role: provider|business (included handler)'
    state='POST' if post else ('GET logout' if rel in ('auth/logout.php','logout.php') else '')
    upload=('upload_image(' in s and 'function upload_image' not in s)
    fetchall=s.count('fetchAll()')
    has_limit='LIMIT ' in s.upper()
    prepared=s.count('->prepare(')
    raw_query=s.count('->query(')
    rows.append({
        'route':rel,'auth':auth,'state_change':state,'csrf_on_post':'yes' if (post and csrf) else ('n/a' if not post else 'no'),
        'upload':'yes' if upload else 'no','fetchAll_calls':fetchall,'contains_limit':'yes' if has_limit else 'no',
        'prepared_calls':prepared,'raw_query_calls':raw_query,
    })
out=ROOT/'docs/production/route_inventory.csv'
with out.open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
print(f'wrote {out.relative_to(ROOT)} with {len(rows)} PHP routes/includes')
