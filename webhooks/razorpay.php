<?php
declare(strict_types=1);
// CSRF_EXEMPT_WEBHOOK: this endpoint is called server-to-server by Razorpay.
// Authentication is the HMAC signature over the exact raw request body, plus an
// optional deployment IP allowlist. No browser session or CSRF token is trusted.
require_once __DIR__.'/../config/database.php';
require_once __DIR__.'/../includes/billing.php';
require_once __DIR__.'/../includes/security.php';

apply_api_security_headers();
if($_SERVER['REQUEST_METHOD']!=='POST'){http_response_code(405);header('Allow: POST');exit;}
enforce_request_body_limit(1048576);
header('Content-Type: application/json; charset=UTF-8');
$raw=(string)file_get_contents('php://input');
$signature=(string)($_SERVER['HTTP_X_RAZORPAY_SIGNATURE']??'');
$eventId=(string)($_SERVER['HTTP_X_RAZORPAY_EVENT_ID']??'');
try{
    $result=process_razorpay_webhook($raw,$signature,$eventId?:null);
    http_response_code(200);echo json_encode(['ok'=>true,'duplicate'=>(bool)$result['duplicate']]);
}catch(Throwable $e){
    $message=$e instanceof RuntimeException?$e->getMessage():'Webhook processing failed.';
    $invalid=str_contains(strtolower($message),'signature')||str_contains(strtolower($message),'allowlist')||str_contains(strtolower($message),'json')||str_contains(strtolower($message),'too large');
    http_response_code($invalid?400:500);
    security_log('razorpay_webhook_rejected',['error_class'=>$e::class]);
    echo json_encode(['ok'=>false]);
}
