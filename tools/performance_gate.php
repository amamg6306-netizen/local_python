<?php
declare(strict_types=1);
if(PHP_SAPI!=='cli'){http_response_code(404);exit;}
require_once __DIR__.'/../config/app.php';
$path=$argv[1]??(__DIR__.'/../storage/logs/performance.log');if(!is_file($path)){fwrite(STDERR,"Performance log not found.\n");exit(2);}
$d=[];$m=[];$fh=fopen($path,'rb');while(($line=fgets($fh))!==false){$r=json_decode($line,true);if(is_array($r)&&isset($r['duration_ms'],$r['memory_peak_bytes'])){$d[]=(float)$r['duration_ms'];$m[]=(int)$r['memory_peak_bytes'];}}fclose($fh);
$min=max(20,env_int('PERF_MIN_SAMPLES',100));if(count($d)<$min){fwrite(STDERR,"FAIL: only ".count($d)." samples; {$min} required.\n");exit(1);}sort($d);sort($m);$pct=static fn(array $a,float $p)=>$a[max(0,min(count($a)-1,(int)ceil($p*count($a))-1))];$p95=$pct($d,.95);$memMb=$pct($m,.95)/1048576;$targetMs=max(50,env_int('PERF_TARGET_P95_MS',750));$targetMb=max(8,env_int('PERF_TARGET_PEAK_MB',32));$ok=$p95<=$targetMs&&$memMb<=$targetMb;printf("%s: samples=%d p95=%.2fms target<=%dms p95_peak=%.2fMiB target<=%dMiB\n",$ok?'PASS':'FAIL',count($d),$p95,$targetMs,$memMb,$targetMb);exit($ok?0:1);
