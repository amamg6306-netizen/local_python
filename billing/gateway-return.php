<?php
declare(strict_types=1);
require_once __DIR__.'/../includes/auth.php';
require_once __DIR__.'/../includes/billing.php';
$user=require_role(['provider','business']);
if($_SERVER['REQUEST_METHOD']!=='POST'){http_response_code(405);header('Allow: POST');exit('Method not allowed.');}
verify_csrf();
try{
    $localId=(int)($_POST['local_payment_id']??0);$p=payment_by_id($localId);if(!$p||(int)$p['user_id']!==(int)$user['id'])throw new RuntimeException('Payment not found.');
    record_verified_gateway_callback($localId,clean_text($_POST['razorpay_order_id']??'',190,true,'Order reference'),clean_text($_POST['razorpay_payment_id']??'',190,true,'Payment reference'),clean_text($_POST['razorpay_signature']??'',128,true,'Signature'));
    flash('success','Gateway confirmation received. Your plan will activate only after the signed server webhook is reconciled.');
}catch(Throwable $e){security_log('gateway_callback_rejected',['user_id'=>(int)$user['id'],'error_class'=>$e::class]);flash('error','Gateway confirmation could not be verified. No subscription was activated.');}
redirect('billing/history.php');
