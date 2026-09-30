<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
require_once __DIR__.'/../config/database.php';
require_once __DIR__.'/../includes/billing.php';
$requested=20;
foreach($argv as $arg){if(preg_match('/^--limit=(\d+)$/',$arg,$m))$requested=(int)$m[1];}
$max=max(1,min(100,env_int('PAYMENT_WORKER_BATCH_MAX',20)));$requested=max(1,min($max,$requested));
try{$stats=run_payment_reconciliation_batch($requested);echo json_encode($stats,JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES).PHP_EOL;exit(($stats['dead']??0)>0?2:0);}catch(Throwable $e){fwrite(STDERR,'Reconciliation worker failed: '.$e->getMessage().PHP_EOL);exit(1);}
