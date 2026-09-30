#!/usr/bin/env python3
from pathlib import Path
import json,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
def run(mode):
 p=subprocess.run(['php',str(ROOT/'tests/phase5/memory_fixture.php'),mode],capture_output=True,text=True,check=True)
 return json.loads(p.stdout)
a=run('unbounded');b=run('bounded')
ratio=(a['peak_bytes']/max(1,b['peak_bytes']))
print(json.dumps({'unbounded_proxy':a,'bounded_proxy':b,'peak_ratio':round(ratio,2)},indent=2))
if b['peak_bytes']>=a['peak_bytes']:
 print('FAIL: bounded fixture did not reduce peak memory',file=sys.stderr);sys.exit(1)
print('PASS: bounded buffering proxy uses less peak memory')
