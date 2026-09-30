#!/usr/bin/env python3
import argparse,concurrent.futures,statistics,time,urllib.request,urllib.error,json,math
p=argparse.ArgumentParser(description='Bounded LocalConnect HTTP latency/concurrency probe')
p.add_argument('--url',required=True);p.add_argument('--requests',type=int,default=200);p.add_argument('--concurrency',type=int,default=10);p.add_argument('--cookie',default='');p.add_argument('--timeout',type=float,default=10.0)
a=p.parse_args();a.requests=max(1,min(a.requests,5000));a.concurrency=max(1,min(a.concurrency,100));
def one(_):
 h={'User-Agent':'LocalConnect-Performance-Probe/1.0'}
 if a.cookie:h['Cookie']=a.cookie
 req=urllib.request.Request(a.url,headers=h,method='GET');t=time.perf_counter();code=0;size=0
 try:
  with urllib.request.urlopen(req,timeout=a.timeout) as r:data=r.read(2_000_000);code=r.status;size=len(data)
 except urllib.error.HTTPError as e: code=e.code
 except Exception: code=-1
 return (time.perf_counter()-t)*1000,code,size
with concurrent.futures.ThreadPoolExecutor(max_workers=a.concurrency) as ex:r=list(ex.map(one,range(a.requests)))
lat=sorted(x[0] for x in r);pct=lambda p:lat[max(0,min(len(lat)-1,math.ceil(p*len(lat))-1))]
out={'requests':a.requests,'concurrency':a.concurrency,'p50_ms':round(pct(.5),2),'p95_ms':round(pct(.95),2),'max_ms':round(max(lat),2),'codes':{},'max_response_bytes':max(x[2] for x in r)}
for _,c,_ in r:out['codes'][str(c)]=out['codes'].get(str(c),0)+1
print(json.dumps(out,indent=2));raise SystemExit(0 if all(200<=c<400 for _,c,_ in r) else 2)
