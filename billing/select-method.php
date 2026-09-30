<?php
declare(strict_types=1);
require_once __DIR__.'/../includes/auth.php';
require_once __DIR__.'/../includes/billing.php';
$user=require_role(['provider','business']);
if($_SERVER['REQUEST_METHOD']!=='POST'){http_response_code(405);header('Allow: POST');exit('Method not allowed.');}
verify_csrf();$token=(string)($_POST['token']??'');$methodId=(int)($_POST['method_id']??0);
try{
    $payment=create_payment_for_intent($token,$user,$methodId);
    if((string)$payment['payment_method_type_snapshot']==='gateway'){
        $payment=create_razorpay_order((int)$payment['id']);
        redirect('billing/gateway.php?token='.rawurlencode($token));
    }
    redirect('billing/manual.php?token='.rawurlencode($token));
}catch(Throwable $e){security_log('checkout_method_failed',['user_id'=>(int)$user['id'],'error_class'=>$e::class]);flash('error',$e instanceof RuntimeException?$e->getMessage():'Payment setup failed.');redirect('billing/history.php');}
