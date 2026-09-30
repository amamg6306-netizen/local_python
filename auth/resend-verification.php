<?php
declare(strict_types=1);
require_once __DIR__.'/../includes/auth.php';
require_guest();
$message='';

if($_SERVER['REQUEST_METHOD']==='POST'){
    verify_csrf();
    $email=strtolower(trim((string)($_POST['email']??'')));
    $retry=auth_action_rate_check('email-verification',$email);
    if($retry<=0){
        auth_action_rate_hit('email-verification',$email,3,900,900);
        if(filter_var($email,FILTER_VALIDATE_EMAIL)){
            $q=db()->prepare("SELECT id,email,email_verified_at,status FROM users WHERE email=? AND status<>'blocked' LIMIT 1");
            $q->execute([$email]);
            if(($u=$q->fetch()) && empty($u['email_verified_at'])){
                $token=create_auth_token((int)$u['id'],'email_verify',86400);
                try{
                    $link=absolute_url('auth/verify-email.php?selector='.rawurlencode($token['selector']).'&token='.rawurlencode($token['token']));
                    send_app_email((string)$u['email'],'Verify your LocalConnect email',"Open this link to verify your account:\n{$link}\n\nThis link expires in 24 hours.");
                }catch(Throwable $e){security_log('verification_delivery_unavailable',['error_class'=>$e::class]);}
            }
        }
    }else{
        security_log('verification_rate_limited',['retry_after'=>$retry]);
    }
    $message='If the account needs verification, a new verification message will be sent.';
}
$pageTitle='Resend verification — LocalConnect';require __DIR__.'/../includes/header.php';?>
<div class="container auth-wrap py-5"><div class="soft-card p-4 p-md-5"><h2 class="fw-bold">Resend verification</h2><?php if($message):?><div class="alert alert-info"><?=e($message)?></div><?php endif;?><form method="post"><?=csrf_field()?><label class="form-label">Email</label><input class="form-control" type="email" name="email" maxlength="190" required autocomplete="email"><button class="btn btn-primary w-100 mt-3">Send verification</button></form></div></div><?php require __DIR__.'/../includes/footer.php';?>
