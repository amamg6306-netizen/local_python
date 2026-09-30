<?php
declare(strict_types=1);
require_once __DIR__ . '/functions.php';

final class PaymentGatewayException extends RuntimeException
{
    public function __construct(string $message, public readonly bool $ambiguous = false, public readonly ?int $httpStatus = null)
    {
        parent::__construct($message);
    }
}

function money_minor(string|int|float $amount): int
{
    $raw = trim((string)$amount);
    if (!preg_match('/^\d+(?:\.\d{1,2})?$/', $raw)) throw new RuntimeException('Invalid money amount.');
    [$whole,$frac] = array_pad(explode('.', $raw, 2), 2, '');
    $frac = str_pad(substr($frac, 0, 2), 2, '0');
    $minor = ((int)$whole * 100) + (int)$frac;
    if ($minor < 0 || $minor > 10000000000) throw new RuntimeException('Money amount is outside the allowed range.');
    return $minor;
}

function money_decimal_from_minor(int $minor): string
{
    if ($minor < 0) throw new RuntimeException('Invalid money amount.');
    return sprintf('%d.%02d', intdiv($minor,100), $minor % 100);
}

function billing_plan_for_role(int $planId, string $role): array
{
    if (!in_array($role, ['provider','business'], true)) throw new RuntimeException('This account cannot purchase subscriptions.');
    $q=db()->prepare("SELECT * FROM subscription_plans WHERE id=? AND is_active=1 AND audience IN (?, 'both') LIMIT 1");
    $q->execute([$planId,$role]);
    $plan=$q->fetch();
    if(!$plan) throw new RuntimeException('The selected plan is unavailable for this account.');
    return $plan;
}

function plan_price_breakdown(array $plan): array
{
    $subtotal=money_minor((string)$plan['price_monthly']);
    $bps=max(0,min(10000,(int)($plan['tax_rate_bps']??0)));
    $tax=(int)round($subtotal*$bps/10000,0,PHP_ROUND_HALF_UP);
    return [
        'currency'=>'INR',
        'subtotal_minor'=>$subtotal,
        'tax_minor'=>$tax,
        'total_minor'=>$subtotal+$tax,
        'subtotal'=>money_decimal_from_minor($subtotal),
        'tax'=>money_decimal_from_minor($tax),
        'total'=>money_decimal_from_minor($subtotal+$tax),
        'tax_label'=>(string)($plan['tax_label']??'Tax'),
        'billing_period_months'=>max(1,min(24,(int)($plan['billing_period_months']??1))),
    ];
}

function checkout_token_hash(string $token): string
{
    if(!preg_match('/^[a-f0-9]{64}$/',$token)) return hash('sha256','invalid-token');
    return hash('sha256',$token);
}

function create_checkout_intent(array $user, int $planId): string
{
    $role=(string)($user['role']??'');
    $plan=billing_plan_for_role($planId,$role);
    $pricing=plan_price_breakdown($plan);
    if($pricing['total_minor']<=0) throw new RuntimeException('The selected plan does not require payment.');

    $token=bin2hex(random_bytes(32));
    $ttl=max(300,min(7200,env_int('PAYMENT_CHECKOUT_TTL_SECONDS',1800)));
    $expires=(new DateTimeImmutable('+'.$ttl.' seconds'))->format('Y-m-d H:i:s');
    $q=db()->prepare('INSERT INTO checkout_intents(token_hash,user_id,user_role,plan_id,plan_code_snapshot,plan_name_snapshot,currency,subtotal_amount,tax_amount,total_amount,billing_period_months,status,expires_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)');
    $q->execute([
        checkout_token_hash($token),(int)$user['id'],$role,(int)$plan['id'],(string)$plan['code'],(string)$plan['name'],'INR',
        $pricing['subtotal'],$pricing['tax'],$pricing['total'],$pricing['billing_period_months'],'selecting_method',$expires
    ]);
    return $token;
}

function expire_checkout_intents(int $userId): void
{
    $q=db()->prepare("UPDATE checkout_intents SET status='expired' WHERE user_id=? AND status IN ('selecting_method','pending_gateway','pending_manual') AND expires_at<NOW()");
    $q->execute([$userId]);
}

function checkout_intent(string $token, int $userId, bool $lock=false): ?array
{
    if(!preg_match('/^[a-f0-9]{64}$/',$token)) return null;
    expire_checkout_intents($userId);
    $sql='SELECT ci.*,p.code plan_code,p.name plan_name,p.description,p.featured_days,p.lead_limit,p.is_active plan_active FROM checkout_intents ci JOIN subscription_plans p ON p.id=ci.plan_id WHERE ci.token_hash=? AND ci.user_id=? LIMIT 1'.($lock?' FOR UPDATE':'');
    $q=db()->prepare($sql);$q->execute([checkout_token_hash($token),$userId]);
    return $q->fetch()?:null;
}

function configured_payment_methods_for_role(string $role,string $currency='INR'): array
{
    $rows=active_payment_methods_for_role($role,$currency);$out=[];
    foreach($rows as $row){$cfg=payment_method_configuration_status($row);if($cfg['configured'])$out[]=$row;}
    return $out;
}

function payment_history_add(int $paymentId, ?string $old, string $new, string $source, ?string $eventKey=null, ?string $note=null, ?int $actorId=null): void
{
    $source=in_array($source,['checkout','callback','webhook','reconciliation','admin','system'],true)?$source:'system';
    $q=db()->prepare('INSERT INTO payment_status_history(payment_id,old_status,new_status,source,external_event_key,note,actor_user_id) VALUES(?,?,?,?,?,?,?)');
    $q->execute([$paymentId,$old,$new,$source,$eventKey,$note!==null?substr($note,0,500):null,$actorId]);
}

function payment_by_id(int $paymentId, bool $lock=false): ?array
{
    $q=db()->prepare('SELECT p.*,pm.gateway_code,pm.display_instructions,pm.merchant_upi_id,pm.bank_beneficiary,pm.bank_reference FROM payments p LEFT JOIN payment_methods pm ON pm.id=p.payment_method_id WHERE p.id=? LIMIT 1'.($lock?' FOR UPDATE':''));
    $q->execute([$paymentId]);return $q->fetch()?:null;
}

function create_payment_for_intent(string $token,array $user,int $methodId): array
{
    $pdo=db();$pdo->beginTransaction();
    try{
        $intent=checkout_intent($token,(int)$user['id'],true);
        if(!$intent || $intent['status']!=='selecting_method') throw new RuntimeException('This checkout is no longer available. Start again from the subscription page.');
        if(strtotime((string)$intent['expires_at'])<time()) throw new RuntimeException('This checkout expired. Start again.');
        if((string)$intent['user_role']!==(string)$user['role']) throw new RuntimeException('Checkout role mismatch.');
        $m=$pdo->prepare("SELECT * FROM payment_methods WHERE id=? AND is_active=1 AND currency=? AND audience IN (?, 'both') LIMIT 1 FOR UPDATE");
        $m->execute([$methodId,(string)$intent['currency'],(string)$user['role']]);$method=$m->fetch();
        if(!$method) throw new RuntimeException('That payment method is not available for this account.');
        $cfg=payment_method_configuration_status($method);if(!$cfg['configured'])throw new RuntimeException('That payment method is temporarily unavailable.');
        $idempotency=bin2hex(random_bytes(32));
        $q=$pdo->prepare('INSERT INTO payments(user_id,plan_id,payment_method_id,payment_method_code_snapshot,payment_method_name_snapshot,payment_method_type_snapshot,manual_instructions_snapshot,merchant_upi_id_snapshot,bank_beneficiary_snapshot,bank_reference_snapshot,plan_code_snapshot,plan_name_snapshot,subtotal_amount,tax_amount,billing_period_months,idempotency_key,provider,amount,currency,status,reconciliation_status,checkout_expires_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)');
        $provider=$method['method_type']==='gateway'?(string)$method['gateway_code']:'manual';
        $q->execute([(int)$user['id'],(int)$intent['plan_id'],(int)$method['id'],(string)$method['code'],(string)$method['name'],(string)$method['method_type'],(string)($method['display_instructions']??''),(string)($method['merchant_upi_id']??''),(string)($method['bank_beneficiary']??''),(string)($method['bank_reference']??''),(string)$intent['plan_code_snapshot'],(string)$intent['plan_name_snapshot'],(string)$intent['subtotal_amount'],(string)$intent['tax_amount'],(int)$intent['billing_period_months'],$idempotency,$provider,(string)$intent['total_amount'],(string)$intent['currency'],'pending','pending',(string)$intent['expires_at']]);
        $paymentId=(int)$pdo->lastInsertId();
        $newIntentStatus=$method['method_type']==='gateway'?'pending_gateway':'pending_manual';
        $u=$pdo->prepare('UPDATE checkout_intents SET payment_id=?,status=? WHERE id=?');$u->execute([$paymentId,$newIntentStatus,(int)$intent['id']]);
        payment_history_add($paymentId,null,'pending','checkout',null,'Payment created from immutable checkout snapshot.',(int)$user['id']);
        $pdo->commit();
        $payment=payment_by_id($paymentId);
        if(!$payment)throw new RuntimeException('Payment could not be loaded.');
        return $payment;
    }catch(Throwable $e){if($pdo->inTransaction())$pdo->rollBack();throw $e;}
}

function razorpay_credentials(): array
{
    $keyId=trim((string)(env_value('PAYMENT_RAZORPAY_KEY_ID','')??''));
    $secret=trim((string)(env_value('PAYMENT_RAZORPAY_KEY_SECRET','')??''));
    $webhook=trim((string)(env_value('PAYMENT_RAZORPAY_WEBHOOK_SECRET','')??''));
    if($keyId===''||$secret===''||$webhook===''||str_contains($keyId,'REPLACE_WITH_')||str_contains($secret,'REPLACE_WITH_')||str_contains($webhook,'REPLACE_WITH_'))throw new RuntimeException('Razorpay sandbox credentials are not configured.');
    if(str_starts_with($keyId,'rzp_live_')&&!env_bool('PAYMENT_ALLOW_LIVE',false))throw new RuntimeException('Live payment credentials are disabled by deployment policy. Use Razorpay Test Mode credentials.');
    return ['key_id'=>$keyId,'key_secret'=>$secret,'webhook_secret'=>$webhook];
}

function razorpay_api_request(string $method,string $path,?array $payload=null): array
{
    $creds=razorpay_credentials();
    if(!function_exists('curl_init'))throw new PaymentGatewayException('PHP cURL is required for gateway API calls.');
    if(!preg_match('#^/[A-Za-z0-9_./-]+$#',$path))throw new InvalidArgumentException('Invalid gateway API path.');
    $url='https://api.razorpay.com/v1'.$path;
    $ch=curl_init($url);if($ch===false)throw new PaymentGatewayException('Payment gateway client could not start.');
    $headers=['Accept: application/json'];
    $opts=[CURLOPT_RETURNTRANSFER=>true,CURLOPT_CUSTOMREQUEST=>strtoupper($method),CURLOPT_USERPWD=>$creds['key_id'].':'.$creds['key_secret'],CURLOPT_HTTPAUTH=>CURLAUTH_BASIC,CURLOPT_CONNECTTIMEOUT=>5,CURLOPT_TIMEOUT=>15,CURLOPT_HTTPHEADER=>$headers];
    if($payload!==null){$body=json_encode($payload,JSON_UNESCAPED_SLASHES);if($body===false)throw new RuntimeException('Gateway payload encoding failed.');$opts[CURLOPT_POSTFIELDS]=$body;$opts[CURLOPT_HTTPHEADER]=['Accept: application/json','Content-Type: application/json'];}
    curl_setopt_array($ch,$opts);$raw=curl_exec($ch);$errno=curl_errno($ch);$status=(int)curl_getinfo($ch,CURLINFO_RESPONSE_CODE);curl_close($ch);
    if($raw===false||$errno!==0)throw new PaymentGatewayException('The payment gateway could not be reached. The transaction was not retried automatically because the remote result may be unknown.',true,null);
    $data=json_decode((string)$raw,true);if(!is_array($data))$data=[];
    if($status<200||$status>=300){
        $safe='The payment gateway rejected the request.';
        if($status>=500||$status===0)throw new PaymentGatewayException('The payment gateway is temporarily unavailable. The transaction needs reconciliation before retry.',true,$status);
        throw new PaymentGatewayException($safe,false,$status);
    }
    return $data;
}

function create_razorpay_order(int $paymentId): array
{
    $payment=payment_by_id($paymentId);if(!$payment)throw new RuntimeException('Payment not found.');
    if((string)$payment['provider']!=='razorpay'||(string)$payment['payment_method_type_snapshot']!=='gateway')throw new RuntimeException('This payment is not a Razorpay gateway payment.');
    if(!empty($payment['provider_order_id']))return $payment;
    $minor=money_minor((string)$payment['amount']);
    $payload=['amount'=>$minor,'currency'=>(string)$payment['currency'],'receipt'=>'lc_pmt_'.$paymentId,'notes'=>['localconnect_payment_id'=>(string)$paymentId,'localconnect_user_id'=>(string)$payment['user_id'],'plan'=>(string)$payment['plan_code_snapshot']]];
    try{$order=razorpay_api_request('POST','/orders',$payload);}catch(PaymentGatewayException $e){
        $pdo=db();$pdo->beginTransaction();try{$locked=payment_by_id($paymentId,true);if($locked&&$locked['status']==='pending'){$old=(string)$locked['status'];if($e->ambiguous){$q=$pdo->prepare("UPDATE payments SET status='requires_review',reconciliation_status='manual_review',reconciliation_note=? WHERE id=?");$q->execute(['Gateway order result is ambiguous; reconcile before retry.',$paymentId]);payment_history_add($paymentId,$old,'requires_review','reconciliation',null,'Gateway order result ambiguous.');}else{$q=$pdo->prepare("UPDATE payments SET status='failed',reconciliation_status='warning',reconciliation_note=?,failed_at=NOW() WHERE id=?");$q->execute(['Gateway rejected order creation.',$paymentId]);payment_history_add($paymentId,$old,'failed','checkout',null,'Gateway rejected order creation.');}}$pdo->commit();}catch(Throwable $inner){if($pdo->inTransaction())$pdo->rollBack();}throw $e;}
    $orderId=(string)($order['id']??'');$amount=(int)($order['amount']??-1);$currency=(string)($order['currency']??'');$receipt=(string)($order['receipt']??'');
    if($orderId===''||$amount!==$minor||$currency!==(string)$payment['currency']||$receipt!=='lc_pmt_'.$paymentId)throw new PaymentGatewayException('Gateway order response did not match the local payment snapshot.',true);
    $q=db()->prepare('UPDATE payments SET provider_order_id=?,reconciliation_status=? WHERE id=? AND provider_order_id IS NULL');$q->execute([$orderId,'pending',$paymentId]);
    return payment_by_id($paymentId)?:$payment;
}

function verify_razorpay_callback_signature(string $orderId,string $paymentId,string $signature): bool
{
    if($orderId===''||$paymentId===''||!preg_match('/^[a-fA-F0-9]{64}$/',$signature))return false;
    $secret=razorpay_credentials()['key_secret'];
    return hash_equals(hash_hmac('sha256',$orderId.'|'.$paymentId,$secret),strtolower($signature));
}

function record_verified_gateway_callback(int $localPaymentId,string $providerOrderId,string $providerPaymentId,string $signature): void
{
    $pdo=db();$pdo->beginTransaction();
    try{$p=payment_by_id($localPaymentId,true);if(!$p)throw new RuntimeException('Payment not found.');if((string)$p['provider_order_id']!==$providerOrderId)throw new RuntimeException('Order mismatch.');if(!verify_razorpay_callback_signature($providerOrderId,$providerPaymentId,$signature))throw new RuntimeException('Payment callback signature is invalid.');
        if(!empty($p['provider_payment_id'])&&!hash_equals((string)$p['provider_payment_id'],$providerPaymentId))throw new RuntimeException('Payment reference mismatch.');
        $q=$pdo->prepare('UPDATE payments SET provider_payment_id=?,gateway_callback_verified_at=COALESCE(gateway_callback_verified_at,NOW()) WHERE id=?');$q->execute([$providerPaymentId,$localPaymentId]);
        payment_history_add($localPaymentId,(string)$p['status'],(string)$p['status'],'callback',null,'Signed browser callback verified; entitlement still waits for signed webhook + server reconciliation.',(int)$p['user_id']);
        $pdo->commit();
    }catch(Throwable $e){if($pdo->inTransaction())$pdo->rollBack();throw $e;}
}

function remote_razorpay_payment(string $paymentId): array
{
    if(!preg_match('/^[A-Za-z0-9_-]{5,190}$/',$paymentId))throw new RuntimeException('Invalid provider payment id.');
    return razorpay_api_request('GET','/payments/'.rawurlencode($paymentId));
}
function remote_razorpay_order(string $orderId): array
{
    if(!preg_match('/^[A-Za-z0-9_-]{5,190}$/',$orderId))throw new RuntimeException('Invalid provider order id.');
    return razorpay_api_request('GET','/orders/'.rawurlencode($orderId));
}

function verify_remote_payment_matches(array $local,array $remotePayment,array $remoteOrder): array
{
    $expected=money_minor((string)$local['amount']);$issues=[];
    if((string)($remotePayment['id']??'')!==(string)$local['provider_payment_id'])$issues[]='payment id mismatch';
    if((string)($remotePayment['order_id']??'')!==(string)$local['provider_order_id'])$issues[]='order id mismatch';
    if((int)($remotePayment['amount']??-1)!==$expected)$issues[]='payment amount mismatch';
    if((string)($remotePayment['currency']??'')!==(string)$local['currency'])$issues[]='payment currency mismatch';
    if((string)($remotePayment['status']??'')!=='captured')$issues[]='payment is not captured';
    if((string)($remoteOrder['id']??'')!==(string)$local['provider_order_id'])$issues[]='remote order id mismatch';
    if((int)($remoteOrder['amount']??-1)!==$expected)$issues[]='order amount mismatch';
    if((string)($remoteOrder['currency']??'')!==(string)$local['currency'])$issues[]='order currency mismatch';
    if((string)($remoteOrder['receipt']??'')!=='lc_pmt_'.(int)$local['id'])$issues[]='order receipt mismatch';
    return $issues;
}

function subscription_end_from(string $start,int $months): string
{
    $dt=new DateTimeImmutable($start);return $dt->modify('+'.max(1,min(24,$months)).' months')->format('Y-m-d H:i:s');
}

function activate_entitlement_for_payment(int $paymentId,string $source='webhook',?string $eventKey=null): int
{
    $pdo=db();$pdo->beginTransaction();
    try{
        $p=payment_by_id($paymentId,true);if(!$p)throw new RuntimeException('Payment not found.');if((string)$p['status']!=='paid')throw new RuntimeException('Only a reconciled paid payment can activate entitlement.');
        if(!empty($p['subscription_id'])){$pdo->commit();return (int)$p['subscription_id'];}
        $lock=$pdo->prepare('SELECT id FROM users WHERE id=? FOR UPDATE');$lock->execute([(int)$p['user_id']]);if(!$lock->fetchColumn())throw new RuntimeException('User not found.');
        $planQ=$pdo->prepare('SELECT * FROM subscription_plans WHERE id=? LIMIT 1');$planQ->execute([(int)$p['plan_id']]);$plan=$planQ->fetch();if(!$plan)throw new RuntimeException('Subscription plan not found.');
        $period=max(1,(int)$p['billing_period_months']);$now=(new DateTimeImmutable())->format('Y-m-d H:i:s');
        $q=$pdo->prepare("SELECT * FROM subscriptions WHERE user_id=? AND status IN ('active','scheduled') ORDER BY starts_at DESC,id DESC FOR UPDATE");$q->execute([(int)$p['user_id']]);$subs=$q->fetchAll();
        $sameLatest=null;$activeOther=[];
        foreach($subs as $s){if((string)$s['plan']===(string)$p['plan_code_snapshot'] && !empty($s['ends_at']) && strtotime((string)$s['ends_at'])>time()){if($sameLatest===null||strtotime((string)$s['ends_at'])>strtotime((string)$sameLatest['ends_at']))$sameLatest=$s;}elseif((string)$s['status']==='active')$activeOther[]=$s;}
        if($sameLatest){$start=(string)$sameLatest['ends_at'];$status='scheduled';}
        else{$start=$now;$status='active';foreach($activeOther as $s){$pdo->prepare("UPDATE subscriptions SET status='expired',ends_at=LEAST(COALESCE(ends_at,NOW()),NOW()) WHERE id=?")->execute([(int)$s['id']]);}}
        $end=subscription_end_from($start,$period);$invoice='LC-'.date('Y').'-'.str_pad((string)$paymentId,8,'0',STR_PAD_LEFT);
        $ins=$pdo->prepare('INSERT INTO subscriptions(user_id,plan,plan_id,source_payment_id,billing_period_months,status,starts_at,ends_at,price,invoice_reference) VALUES(?,?,?,?,?,?,?,?,?,?)');
        $ins->execute([(int)$p['user_id'],(string)$p['plan_code_snapshot'],(int)$p['plan_id'],$paymentId,$period,$status,$start,$end,(string)$p['amount'],$invoice]);$subId=(int)$pdo->lastInsertId();
        $pdo->prepare('UPDATE payments SET subscription_id=?,invoice_reference=? WHERE id=?')->execute([$subId,$invoice,$paymentId]);
        $pdo->prepare("UPDATE checkout_intents SET status='paid' WHERE payment_id=?")->execute([$paymentId]);
        if((int)($plan['featured_days']??0)>0){$fStatus=$status==='active'?'active':'pending';$featuredEnd=(new DateTimeImmutable($start))->modify('+'.(int)$plan['featured_days'].' days')->format('Y-m-d H:i:s');$pdo->prepare('INSERT INTO featured_listings(user_id,subscription_id,status,starts_at,ends_at) VALUES(?,?,?,?,?)')->execute([(int)$p['user_id'],$subId,$fStatus,$start,$featuredEnd]);}
        if($status==='active' && $plan['lead_limit']!==null){$pdo->prepare('INSERT INTO lead_wallets(user_id,credits) VALUES(?,?) ON DUPLICATE KEY UPDATE credits=credits+VALUES(credits)')->execute([(int)$p['user_id'],(int)$plan['lead_limit']]);}
        if($status==='active'){$pdo->prepare('UPDATE subscriptions SET benefits_applied_at=NOW() WHERE id=?')->execute([$subId]);}
        $pdo->prepare('INSERT INTO notifications(user_id,type,title,message,link) VALUES(?,?,?,?,?)')->execute([(int)$p['user_id'],'subscription','Subscription activated',$status==='scheduled'?'Your paid renewal is scheduled after the current entitlement ends.':'Your paid subscription is now active.','billing/history.php']);
        log_activity((int)$p['user_id'],'subscription_entitlement_created','subscription',$subId,'payment_id='.$paymentId.';source='.$source);
        $pdo->commit();return $subId;
    }catch(Throwable $e){if($pdo->inTransaction())$pdo->rollBack();throw $e;}
}

function mark_payment_paid_after_reconciliation(int $paymentId,string $source='reconciliation',?string $eventKey=null,?int $actorId=null): void
{
    $pdo=db();$pdo->beginTransaction();
    try{$p=payment_by_id($paymentId,true);if(!$p)throw new RuntimeException('Payment not found.');
        if(in_array((string)$p['status'],['refunded','disputed'],true))throw new RuntimeException('A refunded/disputed payment cannot be reactivated automatically.');
        $old=(string)$p['status'];if($old!=='paid'){$q=$pdo->prepare("UPDATE payments SET status='paid',reconciliation_status='matched',reconciliation_note=NULL,paid_at=COALESCE(paid_at,NOW()),failed_at=NULL WHERE id=?");$q->execute([$paymentId]);payment_history_add($paymentId,$old,'paid',$source,$eventKey,'Verified server-side reconciliation matched amount, currency and order.',$actorId);} $pdo->commit();
    }catch(Throwable $e){if($pdo->inTransaction())$pdo->rollBack();throw $e;}
    activate_entitlement_for_payment($paymentId,$source,$eventKey);
}

function reconcile_razorpay_payment(int $paymentId,string $source='reconciliation',?string $eventKey=null,?int $actorId=null): array
{
    $p=payment_by_id($paymentId);if(!$p)throw new RuntimeException('Payment not found.');
    if((string)$p['provider']!=='razorpay'||empty($p['provider_order_id'])||empty($p['provider_payment_id']))throw new RuntimeException('Gateway payment references are incomplete.');
    $remotePayment=remote_razorpay_payment((string)$p['provider_payment_id']);$remoteOrder=remote_razorpay_order((string)$p['provider_order_id']);$issues=verify_remote_payment_matches($p,$remotePayment,$remoteOrder);
    if($issues){$note=implode('; ',$issues);$q=db()->prepare("UPDATE payments SET status='requires_review',reconciliation_status='warning',reconciliation_note=? WHERE id=? AND status NOT IN ('refunded','disputed')");$q->execute([substr($note,0,500),$paymentId]);payment_history_add($paymentId,(string)$p['status'],'requires_review',$source,$eventKey,$note,$actorId);throw new RuntimeException('Gateway reconciliation did not match the local payment snapshot.');}
    mark_payment_paid_after_reconciliation($paymentId,$source,$eventKey,$actorId);return ['payment'=>$remotePayment,'order'=>$remoteOrder];
}

function mark_payment_failed(int $paymentId,string $source,?string $eventKey=null,string $note='Payment failed.'): void
{
    $pdo=db();$pdo->beginTransaction();try{$p=payment_by_id($paymentId,true);if(!$p){$pdo->commit();return;}$old=(string)$p['status'];if(in_array($old,['paid','refunded','partially_refunded','disputed'],true)){$pdo->commit();return;}$pdo->prepare("UPDATE payments SET status='failed',reconciliation_status='matched',reconciliation_note=?,failed_at=COALESCE(failed_at,NOW()) WHERE id=?")->execute([substr($note,0,500),$paymentId]);payment_history_add($paymentId,$old,'failed',$source,$eventKey,$note);$pdo->prepare("UPDATE checkout_intents SET status='failed' WHERE payment_id=?")->execute([$paymentId]);$pdo->commit();}catch(Throwable $e){if($pdo->inTransaction())$pdo->rollBack();throw $e;}
}

function revoke_entitlement_for_payment(int $paymentId,string $reason): void
{
    $pdo=db();$pdo->beginTransaction();try{$p=payment_by_id($paymentId,true);if(!$p){$pdo->commit();return;}if(!empty($p['subscription_id'])){$pdo->prepare("UPDATE subscriptions SET status='cancelled',suspension_reason=? WHERE id=? AND status IN ('active','scheduled','suspended')")->execute([substr($reason,0,255),(int)$p['subscription_id']]);}$pdo->commit();}catch(Throwable $e){if($pdo->inTransaction())$pdo->rollBack();throw $e;}
}

function mark_refund_state(int $paymentId,int $amountRefundedMinor,string $eventKey): void
{
    $p=payment_by_id($paymentId);if(!$p)return;$total=money_minor((string)$p['amount']);$full=$amountRefundedMinor>=$total;$new=$full?'refunded':'partially_refunded';$old=(string)$p['status'];
    $q=db()->prepare("UPDATE payments SET status=?,reconciliation_status=?,reconciliation_note=?,refunded_at=CASE WHEN ?='refunded' THEN COALESCE(refunded_at,NOW()) ELSE refunded_at END WHERE id=?");$q->execute([$new,$full?'matched':'manual_review',$full?'Full refund verified from gateway.':'Partial refund requires entitlement review.',$new,$paymentId]);payment_history_add($paymentId,$old,$new,'webhook',$eventKey,$full?'Full refund processed.':'Partial refund processed; entitlement retained pending review.');if($full)revoke_entitlement_for_payment($paymentId,'Payment fully refunded.');
}

function mark_disputed(int $paymentId,string $eventKey,string $note='Gateway dispute opened.'): void
{
    $p=payment_by_id($paymentId);if(!$p)return;$old=(string)$p['status'];$q=db()->prepare("UPDATE payments SET status='disputed',reconciliation_status='manual_review',reconciliation_note=?,disputed_at=COALESCE(disputed_at,NOW()) WHERE id=?");$q->execute([substr($note,0,500),$paymentId]);payment_history_add($paymentId,$old,'disputed','webhook',$eventKey,$note);if(!empty($p['subscription_id']))db()->prepare("UPDATE subscriptions SET status='suspended',suspension_reason=? WHERE id=? AND status IN ('active','scheduled')")->execute(['Payment dispute requires review.',(int)$p['subscription_id']]);
}

function razorpay_webhook_signature_valid(string $rawBody,string $signature): bool
{
    if(!preg_match('/^[a-fA-F0-9]{64}$/',$signature))return false;$secret=razorpay_credentials()['webhook_secret'];return hash_equals(hash_hmac('sha256',$rawBody,$secret),strtolower($signature));
}

function webhook_client_allowed(): bool
{
    $raw=trim((string)(env_value('PAYMENT_RAZORPAY_WEBHOOK_IP_ALLOWLIST','')??''));if($raw==='')return true;$remote=(string)($_SERVER['REMOTE_ADDR']??'');$allowed=array_values(array_filter(array_map('trim',explode(',',$raw))));return in_array($remote,$allowed,true);
}

function webhook_event_identifiers(array $event): array
{
    $payment=$event['payload']['payment']['entity']??[];$refund=$event['payload']['refund']['entity']??[];$dispute=$event['payload']['dispute']['entity']??[];
    $paymentId=(string)($payment['id']??$refund['payment_id']??$dispute['payment_id']??'');$orderId=(string)($payment['order_id']??'');
    return [$paymentId,$orderId];
}

function find_local_payment_by_provider_refs(string $providerPaymentId,string $providerOrderId): ?array
{
    if($providerPaymentId!==''){$q=db()->prepare("SELECT * FROM payments WHERE provider='razorpay' AND provider_payment_id=? LIMIT 1");$q->execute([$providerPaymentId]);if($r=$q->fetch())return $r;}
    if($providerOrderId!==''){$q=db()->prepare("SELECT * FROM payments WHERE provider='razorpay' AND provider_order_id=? LIMIT 1");$q->execute([$providerOrderId]);if($r=$q->fetch())return $r;}
    return null;
}

function enqueue_payment_reconciliation_job(?int $paymentId, int $webhookEventId, string $reason): bool
{
    if ($webhookEventId <= 0) return false;
    $queueMax=max(100,min(100000,env_int('PAYMENT_RECONCILIATION_QUEUE_MAX',10000)));
    $maxAttempts=max(1,min(10,env_int('PAYMENT_WORKER_MAX_ATTEMPTS',5)));
    try{
        $pdo=db();
        $active=(int)$pdo->query("SELECT COUNT(*) FROM payment_reconciliation_jobs WHERE status IN ('queued','processing','retry')")->fetchColumn();
        if($active >= $queueMax){
            security_log('payment_reconciliation_queue_full',['active_jobs'=>$active,'queue_max'=>$queueMax]);
            return false;
        }
        $q=$pdo->prepare("INSERT INTO payment_reconciliation_jobs(webhook_event_id,payment_id,status,attempts,max_attempts,next_attempt_at,last_error) VALUES(?,?,'queued',0,?,NOW(),?) ON DUPLICATE KEY UPDATE payment_id=COALESCE(payment_id,VALUES(payment_id)),last_error=VALUES(last_error)");
        $q->execute([$webhookEventId,$paymentId,$maxAttempts,substr($reason,0,500)]);
        return true;
    }catch(Throwable $e){
        security_log('payment_reconciliation_enqueue_failed',['event_id'=>$webhookEventId,'error_class'=>$e::class]);
        return false;
    }
}

function run_payment_reconciliation_batch(int $requestedLimit=20): array
{
    $limit=max(1,min(max(1,env_int('PAYMENT_WORKER_BATCH_MAX',20)),min(100,$requestedLimit)));
    $pdo=db();
    $pdo->exec("UPDATE payment_reconciliation_jobs SET status='retry',locked_at=NULL,next_attempt_at=NOW(),last_error='Recovered stale processing lease.' WHERE status='processing' AND locked_at < (NOW() - INTERVAL 10 MINUTE) AND attempts < max_attempts");
    $pdo->exec("UPDATE payment_reconciliation_jobs SET status='dead',locked_at=NULL WHERE status IN ('processing','retry','queued') AND attempts >= max_attempts");
    $ids=$pdo->query("SELECT id FROM payment_reconciliation_jobs WHERE status IN ('queued','retry') AND attempts < max_attempts AND next_attempt_at<=NOW() ORDER BY next_attempt_at,id LIMIT ".$limit)->fetchAll(PDO::FETCH_COLUMN);
    $stats=['claimed'=>0,'done'=>0,'retry'=>0,'dead'=>0];
    foreach($ids as $rawId){
        $id=(int)$rawId;
        $claim=$pdo->prepare("UPDATE payment_reconciliation_jobs SET status='processing',attempts=attempts+1,locked_at=NOW() WHERE id=? AND status IN ('queued','retry') AND attempts < max_attempts AND next_attempt_at<=NOW()");
        $claim->execute([$id]);if($claim->rowCount()!==1)continue;$stats['claimed']++;
        $q=$pdo->prepare('SELECT j.*,e.event_type,e.provider_payment_id,e.provider_order_id FROM payment_reconciliation_jobs j LEFT JOIN payment_webhook_events e ON e.id=j.webhook_event_id WHERE j.id=? LIMIT 1');$q->execute([$id]);$job=$q->fetch();
        try{
            if(!$job)throw new RuntimeException('Reconciliation job disappeared.');
            $paymentId=(int)($job['payment_id']??0);
            if($paymentId<=0){$local=find_local_payment_by_provider_refs((string)($job['provider_payment_id']??''),(string)($job['provider_order_id']??''));$paymentId=(int)($local['id']??0);if($paymentId>0)$pdo->prepare('UPDATE payment_reconciliation_jobs SET payment_id=? WHERE id=?')->execute([$paymentId,$id]);}
            if($paymentId<=0)throw new RuntimeException('No local payment matches this webhook yet.');
            $type=(string)($job['event_type']??'');$eventKey='queued:event:'.(int)$job['webhook_event_id'];
            if($type==='payment.captured')reconcile_razorpay_payment($paymentId,'reconciliation',$eventKey);
            elseif($type==='payment.failed')mark_payment_failed($paymentId,'reconciliation',$eventKey,'Queued reconciliation confirmed payment.failed.');
            elseif(str_starts_with($type,'refund.')){$providerPaymentId=(string)($job['provider_payment_id']??'');if($providerPaymentId==='')throw new RuntimeException('Refund event has no provider payment reference.');$remote=remote_razorpay_payment($providerPaymentId);mark_refund_state($paymentId,(int)($remote['amount_refunded']??0),$eventKey);}
            elseif(str_contains($type,'dispute'))mark_disputed($paymentId,$eventKey,'Queued reconciliation processed gateway dispute event.');
            $pdo->prepare("UPDATE payment_reconciliation_jobs SET status='done',locked_at=NULL,last_error=NULL WHERE id=?")->execute([$id]);
            $pdo->prepare("UPDATE payment_webhook_events SET processing_status='processed',processing_note='Recovered by bounded reconciliation worker.',processed_at=NOW() WHERE id=? AND processing_status='failed'")->execute([(int)$job['webhook_event_id']]);
            $stats['done']++;
        }catch(Throwable $e){
            $q=$pdo->prepare('SELECT attempts,max_attempts FROM payment_reconciliation_jobs WHERE id=?');$q->execute([$id]);$attempt=$q->fetch()?:['attempts'=>1,'max_attempts'=>1];$dead=(int)$attempt['attempts']>=(int)$attempt['max_attempts'];
            $backoff=min(3600,30*(2**max(0,(int)$attempt['attempts']-1)));
            $sql=$dead?"UPDATE payment_reconciliation_jobs SET status='dead',locked_at=NULL,last_error=? WHERE id=?":"UPDATE payment_reconciliation_jobs SET status='retry',locked_at=NULL,last_error=?,next_attempt_at=DATE_ADD(NOW(),INTERVAL ".$backoff." SECOND) WHERE id=?";
            $pdo->prepare($sql)->execute([substr($e->getMessage(),0,500),$id]);$stats[$dead?'dead':'retry']++;
            security_log('payment_reconciliation_job_failed',['job_id'=>$id,'error_class'=>$e::class,'dead'=>$dead]);
        }
    }
    return $stats;
}

function process_razorpay_webhook(string $rawBody,string $signature,?string $headerEventId=null): array
{
    if(!webhook_client_allowed())throw new RuntimeException('Webhook source is not allowlisted.');
    if(strlen($rawBody)>1048576)throw new RuntimeException('Webhook payload is too large.');
    if(!razorpay_webhook_signature_valid($rawBody,$signature))throw new RuntimeException('Invalid webhook signature.');
    $event=json_decode($rawBody,true);if(!is_array($event))throw new RuntimeException('Invalid webhook JSON.');$type=(string)($event['event']??'');if($type===''||strlen($type)>120)throw new RuntimeException('Webhook event type is invalid.');
    [$providerPaymentId,$providerOrderId]=webhook_event_identifiers($event);$eventKey=trim((string)$headerEventId);if($eventKey===''||strlen($eventKey)>190)$eventKey=hash('sha256',$rawBody);$hash=hash('sha256',$rawBody);
    $pdo=db();try{$q=$pdo->prepare("INSERT INTO payment_webhook_events(provider,event_key,event_type,payload_sha256,provider_payment_id,provider_order_id,signature_valid,processing_status) VALUES('razorpay',?,?,?,?,?,1,'received')");$q->execute([$eventKey,$type,$hash,$providerPaymentId?:null,$providerOrderId?:null]);}catch(PDOException $e){if(($e->errorInfo[1]??0)===1062){$existing=$pdo->prepare("SELECT id,processing_status,provider_payment_id,provider_order_id FROM payment_webhook_events WHERE provider='razorpay' AND event_key=? LIMIT 1");$existing->execute([$eventKey]);$er=$existing->fetch();if($er&&$er['processing_status']==='failed'){$local=find_local_payment_by_provider_refs((string)($er['provider_payment_id']??''),(string)($er['provider_order_id']??''));if(!enqueue_payment_reconciliation_job(isset($local['id'])?(int)$local['id']:null,(int)$er['id'],'Gateway retried a previously failed webhook event.'))throw new RuntimeException('Reconciliation queue is unavailable or full.');}return ['duplicate'=>true,'processed'=>(bool)($er&&$er['processing_status']==='processed'),'event_key'=>$eventKey];}throw $e;}
    $eventRowId=(int)$pdo->lastInsertId();$status='ignored';$note='Event recorded; no local action required.';
    try{
        $local=find_local_payment_by_provider_refs($providerPaymentId,$providerOrderId);
        if($local && $providerPaymentId!=='' && empty($local['provider_payment_id'])){$pdo->prepare('UPDATE payments SET provider_payment_id=? WHERE id=? AND provider_payment_id IS NULL')->execute([$providerPaymentId,(int)$local['id']]);$local=payment_by_id((int)$local['id'])?:$local;}
        if($type==='payment.captured'){
            if(!$local)throw new RuntimeException('No local payment matches captured gateway references.');
            reconcile_razorpay_payment((int)$local['id'],'webhook',$eventKey);$status='processed';$note='Captured payment reconciled and entitlement processed.';
        }elseif($type==='payment.failed'){
            if($local)mark_payment_failed((int)$local['id'],'webhook',$eventKey,'Gateway reported payment.failed.');$status=$local?'processed':'ignored';$note=$local?'Failed payment recorded.':'No local payment matched failed event.';
        }elseif(str_starts_with($type,'refund.')){
            if($local){$remote=remote_razorpay_payment($providerPaymentId);$amountRefunded=(int)($remote['amount_refunded']??0);mark_refund_state((int)$local['id'],$amountRefunded,$eventKey);$status='processed';$note='Refund state reconciled from gateway payment.';}else{$note='No local payment matched refund event.';}
        }elseif(str_contains($type,'dispute')){
            if($local){mark_disputed((int)$local['id'],$eventKey,'Gateway dispute event: '.$type);$status='processed';$note='Dispute recorded and entitlement suspended pending review.';}else{$note='No local payment matched dispute event.';}
        }
        $pdo->prepare('UPDATE payment_webhook_events SET processing_status=?,processing_note=?,processed_at=NOW() WHERE id=?')->execute([$status,substr($note,0,500),$eventRowId]);return ['duplicate'=>false,'processed'=>$status==='processed','event_key'=>$eventKey,'note'=>$note];
    }catch(Throwable $e){$pdo->prepare("UPDATE payment_webhook_events SET processing_status='failed',processing_note=?,processed_at=NOW() WHERE id=?")->execute([substr($e->getMessage(),0,500),$eventRowId]);$paymentId=isset($local['id'])?(int)$local['id']:null;enqueue_payment_reconciliation_job($paymentId,$eventRowId,$e->getMessage());security_log('payment_webhook_processing_failed',['event_type'=>$type,'event_key'=>$eventKey,'error_class'=>$e::class]);throw $e;}
}

function submit_manual_payment_reference(int $paymentId,array $user,string $reference,string $note): void
{
    $reference=clean_text($reference,190,true,'Payment reference');$note=clean_text($note,500,false,'Note');$pdo=db();$pdo->beginTransaction();try{$p=payment_by_id($paymentId,true);if(!$p||((int)$p['user_id']!==(int)$user['id']))throw new RuntimeException('Payment not found.');if(!in_array((string)$p['payment_method_type_snapshot'],['upi','bank_transfer'],true)||$p['status']!=='pending')throw new RuntimeException('This manual payment is not awaiting a reference.');$q=$pdo->prepare('INSERT INTO manual_payment_submissions(payment_id,user_id,payer_reference,payer_note,status) VALUES(?,?,?,?,\'pending\') ON DUPLICATE KEY UPDATE payer_reference=VALUES(payer_reference),payer_note=VALUES(payer_note),status=IF(status=\'pending\',\'pending\',status)');$q->execute([$paymentId,(int)$user['id'],$reference,$note?:null]);$pdo->prepare("UPDATE payments SET reconciliation_status='manual_review',reconciliation_note='Manual transfer submitted; admin bank/UPI reconciliation required.' WHERE id=?")->execute([$paymentId]);payment_history_add($paymentId,'pending','pending','checkout',null,'Manual payment reference submitted; this is not proof of payment.',(int)$user['id']);$pdo->commit();}catch(Throwable $e){if($pdo->inTransaction())$pdo->rollBack();throw $e;}
}

function verify_manual_payment_admin(int $paymentId,int $adminId,bool $approved,string $note): void
{
    $note=clean_text($note,500,true,'Review note');$pdo=db();$pdo->beginTransaction();try{$p=payment_by_id($paymentId,true);if(!$p)throw new RuntimeException('Payment not found.');$q=$pdo->prepare('SELECT * FROM manual_payment_submissions WHERE payment_id=? LIMIT 1 FOR UPDATE');$q->execute([$paymentId]);$m=$q->fetch();if(!$m||$m['status']!=='pending')throw new RuntimeException('No pending manual payment submission exists.');if($approved){$pdo->prepare("UPDATE manual_payment_submissions SET status='verified',reviewed_by=?,review_note=?,reviewed_at=NOW() WHERE id=?")->execute([$adminId,$note,(int)$m['id']]);$old=(string)$p['status'];$pdo->prepare("UPDATE payments SET status='paid',reconciliation_status='matched',reconciliation_note=?,paid_at=COALESCE(paid_at,NOW()) WHERE id=?")->execute(['Manual transfer verified by authorized admin against external merchant account.',$paymentId]);payment_history_add($paymentId,$old,'paid','admin',null,'Manual payment externally reconciled and approved.',$adminId);}else{$pdo->prepare("UPDATE manual_payment_submissions SET status='rejected',reviewed_by=?,review_note=?,reviewed_at=NOW() WHERE id=?")->execute([$adminId,$note,(int)$m['id']]);$old=(string)$p['status'];$pdo->prepare("UPDATE payments SET status='failed',reconciliation_status='matched',reconciliation_note=?,failed_at=NOW() WHERE id=?")->execute(['Manual payment submission rejected after reconciliation.',$paymentId]);payment_history_add($paymentId,$old,'failed','admin',null,'Manual payment submission rejected.',$adminId);$pdo->prepare("UPDATE checkout_intents SET status='failed' WHERE payment_id=?")->execute([$paymentId]);}$pdo->commit();if($approved)activate_entitlement_for_payment($paymentId,'admin',null);log_activity($adminId,$approved?'manual_payment_verified':'manual_payment_rejected','payment',$paymentId,'Manual reconciliation decision recorded.');}catch(Throwable $e){if($pdo->inTransaction())$pdo->rollBack();throw $e;}
}

function cancel_checkout_payment(int $paymentId,array $user): string
{
    $pdo=db();$pdo->beginTransaction();
    try{
        $p=payment_by_id($paymentId,true);
        if(!$p || (int)$p['user_id']!==(int)$user['id']) throw new RuntimeException('Payment not found.');
        if(!in_array((string)$p['status'],['pending','requires_review'],true)) throw new RuntimeException('This payment can no longer be cancelled from checkout.');
        $m=$pdo->prepare('SELECT status FROM manual_payment_submissions WHERE payment_id=? LIMIT 1 FOR UPDATE');$m->execute([$paymentId]);$manualStatus=$m->fetchColumn();
        $hasExternal=!empty($p['provider_order_id'])||!empty($p['provider_payment_id'])||$manualStatus!==false;
        $old=(string)$p['status'];
        if(!$hasExternal){
            $pdo->prepare("UPDATE payments SET status='cancelled',reconciliation_status='matched',reconciliation_note='Cancelled before any external payment reference existed.',cancelled_at=NOW() WHERE id=?")->execute([$paymentId]);
            $pdo->prepare("UPDATE checkout_intents SET status='cancelled' WHERE payment_id=?")->execute([$paymentId]);
            payment_history_add($paymentId,$old,'cancelled','checkout',null,'Checkout cancelled before an external payment reference existed.',(int)$user['id']);
            $message='Checkout cancelled. No external payment reference had been created.';
        }else{
            $pdo->prepare("UPDATE checkout_intents SET status='cancelled' WHERE payment_id=?")->execute([$paymentId]);
            $pdo->prepare("UPDATE payments SET status='requires_review',reconciliation_status='manual_review',reconciliation_note='User stopped checkout after an external reference/submission existed; reconcile before treating it as cancelled.' WHERE id=? AND status IN ('pending','requires_review')")->execute([$paymentId]);
            payment_history_add($paymentId,$old,'requires_review','checkout',null,'Checkout stopped, but external payment state may still change; reconciliation required.',(int)$user['id']);
            $message='Checkout stopped. Because an external order/reference already exists, the payment remains under reconciliation and is not assumed cancelled.';
        }
        $pdo->commit();return $message;
    }catch(Throwable $e){if($pdo->inTransaction())$pdo->rollBack();throw $e;}
}
