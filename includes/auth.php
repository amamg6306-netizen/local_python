<?php
declare(strict_types=1);
require_once __DIR__ . '/../config/app.php';

if (session_status() !== PHP_SESSION_ACTIVE) {
    ini_set('session.use_strict_mode', '1');
    ini_set('session.use_only_cookies', '1');
    ini_set('session.use_trans_sid', '0');
    ini_set('session.cookie_httponly', '1');
    ini_set('session.cookie_samesite', 'Lax');
    ini_set('session.cache_limiter', 'nocache');
    $secure = env_bool('SESSION_COOKIE_SECURE', is_production()) || request_is_https();
    session_name(env_value('SESSION_NAME', 'localconnect_session') ?? 'localconnect_session');
    session_set_cookie_params(['lifetime'=>0,'path'=>configured_base_path(),'domain'=>'','httponly'=>true,'samesite'=>'Lax','secure'=>$secure]);
    session_start();
}

require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/functions.php';
require_once __DIR__ . '/performance.php';

function clear_auth_session(bool $destroy = true): void
{
    $_SESSION = [];
    if ($destroy && session_status() === PHP_SESSION_ACTIVE) {
        if (ini_get('session.use_cookies')) {
            $p=session_get_cookie_params();
            setcookie(session_name(),'',time()-42000,$p['path'],$p['domain'] ?? '',(bool)$p['secure'],(bool)$p['httponly']);
        }
        session_destroy();
    }
}

function enforce_session_lifecycle(): void
{
    $now=time();$idle=max(300,env_int('SESSION_IDLE_TIMEOUT',1800));$absolute=max($idle,env_int('SESSION_ABSOLUTE_TIMEOUT',28800));$rotate=max(300,env_int('SESSION_ROTATE_INTERVAL',900));
    $_SESSION['_created_at']=$_SESSION['_created_at']??$now;$_SESSION['_last_activity']=$_SESSION['_last_activity']??$now;$_SESSION['_rotated_at']=$_SESSION['_rotated_at']??$now;
    if(!empty($_SESSION['user_id']) && (($now-(int)$_SESSION['_last_activity'])>$idle || ($now-(int)$_SESSION['_created_at'])>$absolute)){
        clear_auth_session(true);session_start();$_SESSION['_created_at']=$now;$_SESSION['_last_activity']=$now;$_SESSION['_rotated_at']=$now;$_SESSION['flash']['error']='Your session expired. Please login again.';return;
    }
    if(!empty($_SESSION['user_id']) && ($now-(int)$_SESSION['_rotated_at'])>$rotate){session_regenerate_id(true);$_SESSION['_rotated_at']=$now;}
    $_SESSION['_last_activity']=$now;
}
enforce_session_lifecycle();

function current_user(): ?array
{
    static $user = false;
    if ($user !== false) return $user;
    if (empty($_SESSION['user_id'])) return $user = null;
    $stmt=db()->prepare('SELECT id,name,email,phone,role,status,city,state,area,pincode,email_verified_at,session_version,created_at FROM users WHERE id=? LIMIT 1');
    $stmt->execute([(int)$_SESSION['user_id']]);$row=$stmt->fetch();
    $sessionVersion=(int)($_SESSION['session_version']??0);
    if(!$row || $row['status']==='blocked' || ($sessionVersion>0 && (int)$row['session_version']!==$sessionVersion)){
        clear_auth_session(true);return $user=null;
    }
    return $user=$row;
}
function is_logged_in(): bool { return current_user() !== null; }
function require_guest(): void { if(($u=current_user()))redirect(dashboard_for($u['role'])); }
function require_login(): array { $u=current_user();if(!$u){flash('error','Please login to continue.');redirect('auth/login.php');}return $u; }

function admin_mfa_record(int $userId): ?array
{
    try{$q=db()->prepare('SELECT * FROM admin_mfa WHERE user_id=? LIMIT 1');$q->execute([$userId]);return $q->fetch()?:null;}catch(Throwable $e){return null;}
}
function admin_mfa_needed(array $u): bool
{
    if(($u['role']??'')!=='admin')return false;$record=admin_mfa_record((int)$u['id']);return $record!==null || env_bool('APP_ADMIN_MFA_REQUIRED',is_production());
}
function admin_mfa_verified(array $u): bool { return (int)($_SESSION['admin_mfa_user_id']??0)===(int)$u['id'] && !empty($_SESSION['admin_mfa_verified_at']); }
function require_role(string|array $roles): array
{
    $u=require_login();$roles=(array)$roles;
    if(!in_array($u['role'],$roles,true)){http_response_code(403);include __DIR__.'/../403.php';exit;}
    if($u['role']==='admin' && admin_mfa_needed($u) && !admin_mfa_verified($u))redirect('admin/mfa.php');
    return $u;
}
function require_recent_admin_reauth(string $returnPath, int $maxAge=600): void
{
    $u=require_role('admin');$ok=(int)($_SESSION['admin_reauth_user_id']??0)===(int)$u['id'] && (time()-(int)($_SESSION['admin_reauth_at']??0))<=$maxAge;
    if(!$ok)redirect('admin/reauth.php?return='.rawurlencode(safe_admin_return($returnPath)));
}

function require_admin_mfa_for_sensitive(): array
{
    $u=require_login();
    if(($u['role']??'')!=='admin'){http_response_code(403);include __DIR__.'/../403.php';exit;}
    $record=admin_mfa_record((int)$u['id']);
    if(!$record || !admin_mfa_verified($u)){
        flash('error','Enable and verify administrator MFA before changing payment configuration.');
        redirect('admin/mfa.php');
    }
    return $u;
}

function login_rate_keys(string $email): array
{
    return [app_hmac(strtolower(trim($email)),'login-email'), app_hmac(client_ip_hash(),'login-ip')];
}
function login_rate_check(string $email): int
{
    $max=0;$q=db()->prepare('SELECT blocked_until FROM auth_rate_limits WHERE bucket_hash=? LIMIT 1');
    foreach(login_rate_keys($email) as $key){$q->execute([$key]);$until=$q->fetchColumn();if($until){$seconds=strtotime((string)$until)-time();if($seconds>$max)$max=$seconds;}}
    return max(0,$max);
}
function login_rate_failure(string $email): void
{
    $window=max(60,env_int('LOGIN_RATE_WINDOW_SECONDS',900));$limit=max(3,env_int('LOGIN_RATE_MAX_ATTEMPTS',5));$block=max(60,env_int('LOGIN_RATE_BLOCK_SECONDS',900));$pdo=db();
    foreach(login_rate_keys($email) as $key){$pdo->beginTransaction();try{$q=$pdo->prepare('SELECT attempts,window_started_at,blocked_until FROM auth_rate_limits WHERE bucket_hash=? FOR UPDATE');$q->execute([$key]);$row=$q->fetch();$now=time();$attempts=1;$windowStart=$now;$blockedUntil=null;if($row){$existingBlock=!empty($row['blocked_until'])?strtotime((string)$row['blocked_until']):0;$start=strtotime((string)$row['window_started_at']);if($existingBlock>$now){$blockedUntil=date('Y-m-d H:i:s',$existingBlock);$attempts=(int)$row['attempts'];$windowStart=$start;}elseif(($now-$start)<=$window){$attempts=(int)$row['attempts']+1;$windowStart=$start;}if($attempts>=$limit)$blockedUntil=date('Y-m-d H:i:s',$now+$block);$u=$pdo->prepare('UPDATE auth_rate_limits SET attempts=?,window_started_at=?,blocked_until=?,updated_at=NOW() WHERE bucket_hash=?');$u->execute([$attempts,date('Y-m-d H:i:s',$windowStart),$blockedUntil,$key]);}else{$blockedUntil=$limit<=1?date('Y-m-d H:i:s',$now+$block):null;$i=$pdo->prepare('INSERT INTO auth_rate_limits(bucket_hash,attempts,window_started_at,blocked_until) VALUES(?,?,?,?)');$i->execute([$key,1,date('Y-m-d H:i:s',$now),$blockedUntil]);}$pdo->commit();}catch(Throwable $e){if($pdo->inTransaction())$pdo->rollBack();security_log('login_rate_write_failed',['error_class'=>$e::class]);}}
}
function login_rate_success(string $email): void
{
    $q=db()->prepare('DELETE FROM auth_rate_limits WHERE bucket_hash=?');foreach(login_rate_keys($email) as $key)$q->execute([$key]);
}


function auth_action_rate_keys(string $action, string $email): array
{
    $action = preg_replace('/[^a-z0-9_-]/i', '', strtolower($action)) ?: 'auth-action';
    $normalized = strtolower(trim($email));
    return [
        app_hmac($action . "\0" . $normalized, 'auth-action-email'),
        app_hmac($action . "\0" . client_ip_hash(), 'auth-action-ip'),
    ];
}

function auth_action_rate_check(string $action, string $email): int
{
    $max = 0;
    $q = db()->prepare('SELECT blocked_until FROM auth_rate_limits WHERE bucket_hash=? LIMIT 1');
    foreach (auth_action_rate_keys($action, $email) as $key) {
        $q->execute([$key]);
        $until = $q->fetchColumn();
        if ($until) $max = max($max, strtotime((string)$until) - time());
    }
    return max(0, $max);
}

function auth_action_rate_hit(string $action, string $email, int $limit = 3, int $window = 900, int $block = 900): void
{
    $limit = max(1, min(20, $limit));
    $window = max(60, min(86400, $window));
    $block = max(60, min(86400, $block));
    $pdo = db();
    foreach (auth_action_rate_keys($action, $email) as $key) {
        $pdo->beginTransaction();
        try {
            $q=$pdo->prepare('SELECT attempts,window_started_at,blocked_until FROM auth_rate_limits WHERE bucket_hash=? FOR UPDATE');
            $q->execute([$key]);$row=$q->fetch();$now=time();$attempts=1;$windowStart=$now;$blockedUntil=null;
            if($row){
                $existingBlock=!empty($row['blocked_until'])?strtotime((string)$row['blocked_until']):0;
                $start=strtotime((string)$row['window_started_at']);
                if($existingBlock>$now){$blockedUntil=date('Y-m-d H:i:s',$existingBlock);$attempts=(int)$row['attempts'];$windowStart=$start;}
                elseif(($now-$start)<=$window){$attempts=(int)$row['attempts']+1;$windowStart=$start;}
                if($attempts>=$limit)$blockedUntil=date('Y-m-d H:i:s',$now+$block);
                $u=$pdo->prepare('UPDATE auth_rate_limits SET attempts=?,window_started_at=?,blocked_until=?,updated_at=NOW() WHERE bucket_hash=?');
                $u->execute([$attempts,date('Y-m-d H:i:s',$windowStart),$blockedUntil,$key]);
            }else{
                $blockedUntil=$limit<=1?date('Y-m-d H:i:s',$now+$block):null;
                $i=$pdo->prepare('INSERT INTO auth_rate_limits(bucket_hash,attempts,window_started_at,blocked_until) VALUES(?,?,?,?)');
                $i->execute([$key,1,date('Y-m-d H:i:s',$now),$blockedUntil]);
            }
            $pdo->commit();
        }catch(Throwable $e){
            if($pdo->inTransaction())$pdo->rollBack();
            security_log('auth_action_rate_write_failed',['action'=>$action,'error_class'=>$e::class]);
        }
    }
}
