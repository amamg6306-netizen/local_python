<?php
declare(strict_types=1);
if(PHP_SAPI!=='cli'){http_response_code(404);exit;}
$path=$argv[1]??(__DIR__.'/../storage/logs/performance.log');
if(!is_file($path)){fwrite(STDERR,"Performance log not found: {$path}\n");exit(1);}
$dur=[];$mem=[];$status=[];$routes=[];$fh=fopen($path,'rb');
while(($line=fgets($fh))!==false){$r=json_decode($line,true);if(!is_array($r)||!isset($r['duration_ms'],$r['memory_peak_bytes']))continue;$dur[]=(float)$r['duration_ms'];$mem[]=(int)$r['memory_peak_bytes'];$status[(string)($r['status']??0)]=($status[(string)($r['status']??0)]??0)+1;$route=(string)($r['route']??'unknown');$routes[$route]=($routes[$route]??0)+1;}fclose($fh);
if(!$dur){fwrite(STDERR,"No valid telemetry records.\n");exit(1);}sort($dur);sort($mem);$pct=static function(array $a,float $p){$i=(int)ceil($p*count($a))-1;return $a[max(0,min(count($a)-1,$i))];};arsort($routes);
$out=['samples'=>count($dur),'latency_ms'=>['p50'=>$pct($dur,.50),'p95'=>$pct($dur,.95),'max'=>max($dur)],'peak_memory_mb'=>['p50'=>round($pct($mem,.50)/1048576,2),'p95'=>round($pct($mem,.95)/1048576,2),'max'=>round(max($mem)/1048576,2)],'http_statuses'=>$status,'top_routes'=>array_slice($routes,0,10,true)];
echo json_encode($out,JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES).PHP_EOL;
