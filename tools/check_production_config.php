<?php
declare(strict_types=1);
if(PHP_SAPI!=='cli'){http_response_code(404);exit;}
require_once __DIR__.'/../config/app.php';
$errors=production_config_errors();
if(app_env()!=='production')$errors[]='APP_ENV is not production.';
foreach(['pdo_mysql','fileinfo','openssl','gd','curl'] as $ext)if(!extension_loaded($ext))$errors[]='Missing PHP extension: '.$ext;
$mail=strtolower((string)(env_value('APP_MAIL_DRIVER','disabled')??'disabled'));
if($mail==='disabled'||$mail==='log')$errors[]='Production mail delivery must be configured and verified.';
if($errors){foreach(array_values(array_unique($errors)) as $e)fwrite(STDERR,"FAIL: {$e}\n");exit(1);}
fwrite(STDOUT,"PASS: production configuration prerequisites are present (secret values not printed).\n");
