<?php
declare(strict_types=1);
putenv('APP_ENV=development');
putenv('PAYMENT_RAZORPAY_KEY_ID=');
putenv('PAYMENT_RAZORPAY_KEY_SECRET=');
putenv('PAYMENT_RAZORPAY_WEBHOOK_SECRET=');
require __DIR__.'/../../config/app.php';
require __DIR__.'/../../includes/functions.php';
$fail=0;
$check=function(bool $ok,string $name)use(&$fail){echo($ok?'PASS':'FAIL').": {$name}\n";if(!$ok)$fail++;};
$check(valid_upi_id('merchant@bank'),'valid UPI ID accepted');
$check(!valid_upi_id('https://example.com'),'URL is not accepted as UPI ID');
$check(!valid_upi_id('bad value@bank'),'invalid UPI ID rejected');
try{$check(normalize_currency('inr')==='INR','INR normalization');}catch(Throwable $e){$check(false,'INR normalization');}
try{normalize_currency('USD');$check(false,'unsupported currency rejected');}catch(RuntimeException $e){$check(true,'unsupported currency rejected');}
$st=payment_gateway_configuration_status('razorpay');
$check($st['configured']===false,'gateway incomplete without server secrets');
putenv('PAYMENT_RAZORPAY_KEY_ID=rzp_test_example');
putenv('PAYMENT_RAZORPAY_KEY_SECRET=sandbox-secret-not-output');
putenv('PAYMENT_RAZORPAY_WEBHOOK_SECRET=sandbox-webhook-not-output');
$st=payment_gateway_configuration_status('razorpay');
$check($st['configured']===true,'gateway configured when all required environment values exist');
$serialized=json_encode($st);
$check(!str_contains($serialized,'sandbox-secret-not-output')&&!str_contains($serialized,'sandbox-webhook-not-output'),'gateway status never returns secret values');
$snap=payment_method_audit_snapshot(['id'=>1,'code'=>'x','name'=>'X','gateway_secret'=>'NEVER','card_number'=>'4111111111111111']);
$check(!array_key_exists('gateway_secret',$snap)&&!array_key_exists('card_number',$snap),'audit snapshot excludes unapproved secret/card fields');
$check(payment_method_configuration_status(['method_type'=>'upi','merchant_upi_id'=>'merchant@bank','display_instructions'=>'Pay and keep reference'])['configured']===true,'manual UPI configuration check');
$check(payment_method_configuration_status(['method_type'=>'bank_transfer','bank_beneficiary'=>'LocalConnect Pvt Ltd','display_instructions'=>'Use invoice reference'])['configured']===true,'manual bank configuration check');
exit($fail?1:0);
