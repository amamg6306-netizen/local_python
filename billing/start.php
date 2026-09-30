<?php
declare(strict_types=1);
require_once __DIR__.'/../includes/auth.php';
require_once __DIR__.'/../includes/billing.php';
$user=require_role(['provider','business']);
if($_SERVER['REQUEST_METHOD']!=='POST'){http_response_code(405);header('Allow: POST');exit('Method not allowed.');}
verify_csrf();
try{
    $planId=(int)($_POST['plan_id']??0);if($planId<=0)throw new RuntimeException('Please choose a valid plan.');
    $plan=billing_plan_for_role($planId,(string)$user['role']);
    $current=current_subscription((int)$user['id']);
    if($current && (string)$current['plan']===(string)$plan['code'])throw new RuntimeException('That is already your current plan.');
    $price=plan_price_breakdown($plan);if($price['total_minor']<=0)throw new RuntimeException('This plan does not require checkout.');
    $token=create_checkout_intent($user,$planId);
    redirect('billing/payment-method.php?token='.rawurlencode($token));
}catch(Throwable $e){flash('error',$e instanceof RuntimeException?$e->getMessage():'Checkout could not be started.');redirect(($user['role']==='business'?'business':'provider').'/subscription.php');}
