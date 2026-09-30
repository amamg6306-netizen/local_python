<?php
declare(strict_types=1);
if(PHP_SAPI!=='cli'){http_response_code(404);exit;}
require_once __DIR__.'/../config/database.php';
$name=getenv('LOCALCONNECT_ADMIN_NAME')?:'';$email=strtolower(getenv('LOCALCONNECT_ADMIN_EMAIL')?:'');$password=getenv('LOCALCONNECT_ADMIN_PASSWORD')?:'';
if(strlen($name)<2||!filter_var($email,FILTER_VALIDATE_EMAIL)||strlen($password)<16){fwrite(STDERR,"Set LOCALCONNECT_ADMIN_NAME, LOCALCONNECT_ADMIN_EMAIL and a >=16 character LOCALCONNECT_ADMIN_PASSWORD in the process environment.\n");exit(2);}
$q=db()->prepare('SELECT id FROM users WHERE email=? LIMIT 1');$q->execute([$email]);if($q->fetch()){fwrite(STDERR,"Account already exists; no change made.\n");exit(3);} $q=db()->prepare("INSERT INTO users(name,email,password_hash,role,status,email_verified_at) VALUES(?,?,?,'admin','active',NOW())");$q->execute([$name,$email,password_hash($password,PASSWORD_DEFAULT)]);fwrite(STDOUT,"Admin account created. Enable MFA immediately at /admin/mfa.php.\n");
