#!/usr/bin/env python3
from pathlib import Path
import re, json, argparse
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(); parser.add_argument('--json',action='store_true'); args=parser.parse_args()
urls=[]
for p in ROOT.rglob('*.php'):
    if any(x in p.parts for x in ('tests','tools','docs')): continue
    text=p.read_text(errors='ignore')
    for u in re.findall(r'https://[^\"\'\s<>]+',text): urls.append({'file':str(p.relative_to(ROOT)),'url':u})
unique=[]; seen=set()
for x in urls:
    k=(x['file'],x['url'])
    if k not in seen: seen.add(k); unique.append(x)
checks=[]
def add(ok,msg): checks.append({'ok':ok,'message':msg})
header=(ROOT/'includes/header.php').read_text()
add('bootstrap@5.3.3' in header,'Bootstrap CDN is version pinned to 5.3.3')
add('font-awesome/6.5.2' in header,'Font Awesome CDN is version pinned to 6.5.2')
gateway=(ROOT/'billing/gateway.php').read_text()
add('https://checkout.razorpay.com/v1/checkout.js' in gateway,'Razorpay hosted checkout script is the documented vendor-managed exception')
add(not (ROOT/'composer.lock').exists(),'No Composer dependency lock is present; application currently has no Composer package supply chain')
result={'dependencies':unique,'checks':checks,'all_checks_pass':all(x['ok'] for x in checks)}
if args.json: print(json.dumps(result,indent=2))
else:
    for c in checks: print(('PASS' if c['ok'] else 'FAIL')+': '+c['message'])
    print('External URL references:')
    for x in unique: print(f"  {x['file']}: {x['url']}")
raise SystemExit(0 if result['all_checks_pass'] else 1)
