<?php
declare(strict_types=1);
require_once __DIR__.'/../includes/auth.php';
require_once __DIR__.'/../includes/billing.php';
$user=require_role(['provider','business']);
if($_SERVER['REQUEST_METHOD']!=='POST'){http_response_code(405);header('Allow: POST');exit('Method not allowed.');}
verify_csrf();
try{$id=(int)($_POST['payment_id']??0);if($id<=0)throw new RuntimeException('Invalid payment.');flash('success',cancel_checkout_payment($id,$user));}
catch(Throwable $e){flash('error',$e instanceof RuntimeException?$e->getMessage():'Checkout could not be cancelled.');}
redirect('billing/history.php');
