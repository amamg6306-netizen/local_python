<?php
declare(strict_types=1);putenv('APP_ENV=development');putenv('APP_KEY=base64:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=');require __DIR__.'/../../config/app.php';require __DIR__.'/../../includes/functions.php';$fail=0;$assert=function($ok,$name)use(&$fail){echo($ok?'PASS':'FAIL').": {$name}\n";if(!$ok)$fail++;};
$assert(base32_decode_secret(base32_encode_secret("12345678901234567890"))==="12345678901234567890",'base32 round trip');
$secret='JBSWY3DPEHPK3PXP';$now=1700000000;$code=totp_code($secret,$now);$assert((bool)preg_match('/^\d{6}$/',$code),'TOTP format');
$assert(hash_equals($code,totp_code($secret,$now)),'TOTP deterministic for same step');
$enc=encrypt_sensitive('phase2-secret');$assert(decrypt_sensitive($enc['ciphertext'],$enc['nonce'],$enc['alg'])==='phase2-secret','secret encrypt/decrypt round trip');
$assert(safe_admin_return('admin/payments.php')==='admin/payments.php','safe admin return allowed');$assert(safe_admin_return('https://evil.example')==='admin/index.php','external return rejected');
try{clean_text(str_repeat('x',11),10,true,'Field');$assert(false,'length validation');}catch(RuntimeException $e){$assert(true,'length validation');}
exit($fail?1:0);
