<?php
declare(strict_types=1);
if(PHP_SAPI!=='cli'){http_response_code(404);exit;}
require_once __DIR__.'/../config/app.php';

$root=dirname(__DIR__);
$blockers=[];$notes=[];
if(app_env()!=='production')$blockers[]='APP_ENV is not production.';
foreach(production_config_errors() as $e)$blockers[]=$e;
foreach(['pdo_mysql','fileinfo','openssl'] as $ext)if(!extension_loaded($ext))$blockers[]="Required PHP extension missing: {$ext}.";
if(!extension_loaded('gd'))$blockers[]='PHP GD extension is required because UPLOAD_REQUIRE_REENCODE is a production gate.';
if(!extension_loaded('curl'))$blockers[]='PHP cURL extension is required for Razorpay API reconciliation.';
if(strtolower((string)(env_value('APP_MAIL_DRIVER','disabled')??'disabled'))==='disabled')$blockers[]='Production email delivery is disabled.';
$liveAllowed=env_bool('PAYMENT_ALLOW_LIVE',false);
if($liveAllowed)$notes[]='PAYMENT_ALLOW_LIVE is already enabled; keep checkout traffic administratively gated until all release checks are complete.';
else $notes[]='PAYMENT_ALLOW_LIVE remains false (safe default). A successful pre-live gate means it may be enabled only during the approved cutover.';

$evidence=[
 'migration-rehearsal.json'=>'database migration + rollback rehearsal',
 'backup-restore.json'=>'backup + restore rehearsal',
 'mail-delivery.json'=>'password-reset/email-verification delivery test',
 'sandbox-payment.json'=>'provider and business sandbox checkout/webhook/reconciliation acceptance',
 'performance.json'=>'representative load/memory performance gate',
 'security-review.json'=>'independent security review / penetration test',
 'legal-financial-review.json'=>'billing, tax and refund policy legal/financial review',
 'production-smoke.json'=>'production smoke test after deployment',
];
foreach($evidence as $file=>$label){
    $path=$root.'/storage/release_evidence/'.$file;
    if(!is_file($path)){$blockers[]="Missing release evidence: {$label} ({$file}).";continue;}
    $data=json_decode((string)file_get_contents($path),true);
    if(!is_array($data)||($data['status']??'')!=='verified'||trim((string)($data['verified_by']??''))===''||trim((string)($data['verified_at']??''))===''||trim((string)($data['reference']??''))===''){
        $blockers[]="Invalid/incomplete release evidence: {$label} ({$file}).";
    }
}

$fresh=(string)@file_get_contents($root.'/database/production/fresh_schema.sql');
if(stripos($fresh,'@localconnect.test')!==false)$blockers[]='Production fresh schema contains a demo/test account.';
if(stripos($fresh,'DROP TABLE IF EXISTS')!==false)$blockers[]='Production fresh schema contains destructive DROP TABLE statements.';

$ready=count($blockers)===0;
$status=$ready?($liveAllowed?'READY_FOR_CONTROLLED_LIVE_CUTOVER':'READY_FOR_LIVE_ENABLEMENT'):'NOT_READY_FOR_LIVE_PAYMENTS';
$out=['status'=>$status,'ready'=>$ready,'blockers'=>$blockers,'notes'=>$notes];
if(in_array('--json',$argv,true))echo json_encode($out,JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES).PHP_EOL;
else{
    echo 'LocalConnect release gate: '.$out['status'].PHP_EOL;
    foreach($blockers as $b)echo 'BLOCKER: '.$b.PHP_EOL;
    foreach($notes as $n)echo 'NOTE: '.$n.PHP_EOL;
}
exit($ready?0:2);
