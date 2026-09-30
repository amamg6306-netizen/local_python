<?php
declare(strict_types=1);
putenv('APP_ENV=development');
putenv('PAYMENT_ALLOW_LIVE=false');
putenv('PAYMENT_RAZORPAY_KEY_ID=rzp_test_example');
putenv('PAYMENT_RAZORPAY_KEY_SECRET=test_secret_value');
putenv('PAYMENT_RAZORPAY_WEBHOOK_SECRET=test_webhook_value');
require __DIR__.'/../../config/app.php';
require __DIR__.'/../../includes/functions.php';
require __DIR__.'/../../includes/billing.php';
$fail=0;
$check=function(bool $ok,string $name)use(&$fail){echo($ok?'PASS':'FAIL').": {$name}\n";if(!$ok)$fail++;};
$check(money_minor('499.00')===49900,'money converted to minor units exactly');
$check(money_decimal_from_minor(49901)==='499.01','minor units converted to decimal exactly');
try{money_minor('1.234');$check(false,'money rejects >2 decimals');}catch(RuntimeException $e){$check(true,'money rejects >2 decimals');}
$price=plan_price_breakdown(['price_monthly'=>'499.00','tax_rate_bps'=>1800,'tax_label'=>'Tax','billing_period_months'=>1]);
$check($price['subtotal_minor']===49900 && $price['tax_minor']===8982 && $price['total_minor']===58882,'server price/tax snapshot math');
$order='order_TEST123';$payment='pay_TEST123';$sig=hash_hmac('sha256',$order.'|'.$payment,'test_secret_value');
$check(verify_razorpay_callback_signature($order,$payment,$sig),'Razorpay callback signature accepted');
$check(!verify_razorpay_callback_signature($order,$payment,str_repeat('0',64)),'bad callback signature rejected');
$raw='{"event":"payment.captured","payload":{}}';$ws=hash_hmac('sha256',$raw,'test_webhook_value');
$check(razorpay_webhook_signature_valid($raw,$ws),'webhook HMAC accepted');
$check(!razorpay_webhook_signature_valid($raw,str_repeat('f',64)),'bad webhook HMAC rejected');
putenv('PAYMENT_RAZORPAY_KEY_ID=rzp_live_example');
$st=payment_gateway_configuration_status('razorpay');
$check($st['configured']===false,'live key blocked while PAYMENT_ALLOW_LIVE=false');
try{razorpay_credentials();$check(false,'live credential guard throws');}catch(RuntimeException $e){$check(true,'live credential guard throws');}
$check(checkout_token_hash(str_repeat('a',64))===hash('sha256',str_repeat('a',64)),'checkout token stored only as hash');
exit($fail?1:0);
