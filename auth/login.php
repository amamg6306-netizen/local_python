<?php
require_once __DIR__.'/../includes/auth.php';require_guest();$error='';
if($_SERVER['REQUEST_METHOD']==='POST'){
    verify_csrf();
    $email=strtolower(clean_text($_POST['email']??'',190,true,'Email'));$password=is_string($_POST['password']??null)?$_POST['password']:'';
    $retry=login_rate_check($email);
    if($retry>0){$error='Too many login attempts. Please wait a few minutes and try again.';security_log('login_rate_limited',['retry_after'=>$retry]);}
    else{
        $stmt=db()->prepare('SELECT id,password_hash,status,email_verified_at,session_version,role FROM users WHERE email=? LIMIT 1');$stmt->execute([$email]);$u=$stmt->fetch();
        $dummy='$2y$12$uDoS0Zr9A82jM9o2GLyA5uFMS4.vEs9f4fKfD6vY9B5oN8Tw3uM9m';
        $valid=$u?password_verify($password,(string)$u['password_hash']):password_verify($password,$dummy);
        if(!$u||!$valid){login_rate_failure($email);$error='Invalid email or password.';security_log('login_failed');}
        elseif($u['status']==='blocked'){$error='This account has been blocked. Please contact support.';security_log('blocked_login',['user_id'=>(int)$u['id']]);}
        elseif($u['status']==='pending' && env_bool('APP_REQUIRE_EMAIL_VERIFICATION',is_production())){$error='Please verify your email address before logging in.';}
        else{
            login_rate_success($email);
            if(password_needs_rehash((string)$u['password_hash'],PASSWORD_DEFAULT)){
                $newHash=password_hash($password,PASSWORD_DEFAULT);
                if(is_string($newHash)&&$newHash!=='')db()->prepare('UPDATE users SET password_hash=? WHERE id=?')->execute([$newHash,(int)$u['id']]);
            }
            session_regenerate_id(true);$_SESSION['user_id']=(int)$u['id'];$_SESSION['session_version']=(int)$u['session_version'];$_SESSION['_created_at']=time();$_SESSION['_last_activity']=time();$_SESSION['_rotated_at']=time();unset($_SESSION['csrf_token'],$_SESSION['admin_mfa_user_id'],$_SESSION['admin_mfa_verified_at']);
            db()->prepare('UPDATE users SET last_login_at=NOW() WHERE id=?')->execute([(int)$u['id']]);log_activity((int)$u['id'],'auth_login','user',(int)$u['id']);
            $full=current_user();if($full && $full['role']==='admin' && admin_mfa_needed($full))redirect('admin/mfa.php');
            flash('success','Welcome back, '.($full['name']??'user').'!');redirect(dashboard_for((string)($full['role']??$u['role'])));
        }
    }
}
$pageTitle='Login — LocalConnect';require __DIR__.'/../includes/header.php';?>
<div class="container auth-wrap py-5"><div class="soft-card p-4 p-md-5"><h2 class="fw-bold">Welcome back</h2><p class="text-muted">Login to your LocalConnect account.</p><?php if($error):?><div class="alert alert-danger"><?=e($error)?></div><?php endif;?><form method="post"><?=csrf_field()?><div class="mb-3"><label class="form-label">Email</label><input class="form-control form-control-lg" type="email" name="email" maxlength="190" required autocomplete="email"></div><div class="mb-3"><label class="form-label">Password</label><input class="form-control form-control-lg" type="password" name="password" required autocomplete="current-password"></div><button class="btn btn-primary btn-lg w-100">Login</button></form><div class="d-flex justify-content-between mt-3"><a href="<?=e(base_url('auth/forgot-password.php'))?>">Forgot password?</a><a href="<?=e(base_url('auth/resend-verification.php'))?>">Resend verification</a></div><p class="text-center text-muted mt-3 mb-0">New here? <a href="<?=e(base_url('auth/register.php'))?>">Create account</a></p></div></div>
<?php require __DIR__.'/../includes/footer.php'; ?>
