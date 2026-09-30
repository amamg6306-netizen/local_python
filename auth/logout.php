<?php
require_once __DIR__.'/../includes/auth.php';
if($_SERVER['REQUEST_METHOD']!=='POST'){http_response_code(405);header('Allow: POST');exit('Method Not Allowed');}
verify_csrf();$u=current_user();if($u)log_activity((int)$u['id'],'auth_logout','user',(int)$u['id']);clear_auth_session(true);session_start();$_SESSION['flash']['success']='You have been logged out.';redirect('auth/login.php');
