<?php
declare(strict_types=1);
require_once __DIR__.'/../includes/auth.php';
require_guest();
$message='';

if($_SERVER['REQUEST_METHOD']==='POST'){
    verify_csrf();
    $email=strtolower(trim((string)($_POST['email']??'')));
    $retry=auth_action_rate_check('password-reset',$email);
    if($retry<=0){
        auth_action_rate_hit('password-reset',$email,3,900,900);
        if(filter_var($email,FILTER_VALIDATE_EMAIL)){
            $q=db()->prepare("SELECT id,email FROM users WHERE email=? AND status<>'blocked' LIMIT 1");
            $q->execute([$email]);
            if($u=$q->fetch()){
                $token=create_auth_token((int)$u['id'],'password_reset',3600);
                try{
                    $link=absolute_url('auth/reset-password.php?selector='.rawurlencode($token['selector']).'&token='.rawurlencode($token['token']));
                    send_app_email((string)$u['email'],'Reset your LocalConnect password',"Open this link to reset your password:\n{$link}\n\nThis link expires in 1 hour.");
                }catch(Throwable $e){security_log('password_reset_delivery_unavailable',['error_class'=>$e::class]);}
            }
        }
    }else{
        security_log('password_reset_rate_limited',['retry_after'=>$retry]);
    }
    // Intentionally identical response to avoid account enumeration and rate-limit disclosure.
    $message='If that email belongs to an eligible account, password-reset instructions will be sent.';
}
$pageTitle='Forgot password — LocalConnect';require __DIR__.'/../includes/header.php';?>
<div class="container auth-wrap py-5"><div class="soft-card p-4 p-md-5"><h2 class="fw-bold">Reset password</h2><?php if($message):?><div class="alert alert-info"><?=e($message)?></div><?php endif;?><form method="post"><?=csrf_field()?><label class="form-label">Email</label><input class="form-control" type="email" name="email" maxlength="190" required autocomplete="email"><button class="btn btn-primary w-100 mt-3">Send reset instructions</button></form></div></div><?php require __DIR__.'/../includes/footer.php';?>
