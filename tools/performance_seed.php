<?php
declare(strict_types=1);
if(PHP_SAPI!=='cli'){http_response_code(404);exit;}
require_once __DIR__.'/../config/database.php';
if(is_production()){fwrite(STDERR,"Refusing to seed performance data in APP_ENV=production.\n");exit(2);}
$cleanup=in_array('--cleanup',$argv,true);$providers=500;$requests=5000;
foreach($argv as $arg){if(preg_match('/^--providers=(\d+)$/',$arg,$m))$providers=max(1,min(5000,(int)$m[1]));if(preg_match('/^--requests=(\d+)$/',$arg,$m))$requests=max(1,min(100000,(int)$m[1]));}
$pdo=db();
if($cleanup){$pdo->beginTransaction();try{$pdo->exec("DELETE FROM users WHERE email LIKE 'lc_perf_%@example.invalid'");$pdo->commit();echo "Performance seed users/data removed via cascades.\n";}catch(Throwable $e){if($pdo->inTransaction())$pdo->rollBack();throw $e;}exit;}
$service=$pdo->query("SELECT s.id service_id,s.category_id FROM services s WHERE s.is_active=1 ORDER BY s.id LIMIT 1")->fetch();if(!$service)throw new RuntimeException('At least one active service is required.');
$hash=password_hash(bin2hex(random_bytes(24)),PASSWORD_DEFAULT);$pdo->beginTransaction();try{
 $q=$pdo->prepare("INSERT INTO users(name,email,password_hash,role,status,city,state,email_verified_at) VALUES('LC Perf Customer','lc_perf_customer@example.invalid',?,'customer','active','Perf City','Perf State',NOW()) ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id)");$q->execute([$hash]);$customer=(int)$pdo->lastInsertId();if($customer===0){$q=$pdo->query("SELECT id FROM users WHERE email='lc_perf_customer@example.invalid'");$customer=(int)$q->fetchColumn();}
 $insUser=$pdo->prepare("INSERT INTO users(name,email,password_hash,role,status,city,state,email_verified_at) VALUES(?,?,?,'provider','active','Perf City','Perf State',NOW()) ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id)");$insProf=$pdo->prepare("INSERT IGNORE INTO provider_profiles(user_id,headline,service_area,verification_status) VALUES(?,'Performance fixture provider','Perf City','verified')");$insSvc=$pdo->prepare("INSERT IGNORE INTO provider_services(provider_user_id,service_id,title,is_active) VALUES(?,?,?,1)");$providerIds=[];
 for($i=1;$i<=$providers;$i++){$email=sprintf('lc_perf_provider_%06d@example.invalid',$i);$insUser->execute(['LC Perf Provider '.$i,$email,$hash]);$id=(int)$pdo->lastInsertId();if($id===0){$q=$pdo->prepare('SELECT id FROM users WHERE email=?');$q->execute([$email]);$id=(int)$q->fetchColumn();}$providerIds[]=$id;$insProf->execute([$id]);$insSvc->execute([$id,(int)$service['service_id'],'Performance Service']);}
 $insReq=$pdo->prepare("INSERT INTO service_requests(customer_id,provider_id,category_id,service_id,request_type,title,description,location_text,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,DATE_SUB(NOW(),INTERVAL ? SECOND))");
 for($i=0;$i<$requests;$i++){$requirement=($i%2)===1;$provider=$requirement?null:$providerIds[$i%count($providerIds)];$insReq->execute([$customer,$provider,(int)$service['category_id'],(int)$service['service_id'],$requirement?'requirement':'direct','Performance request '.$i,str_repeat('Seeded request description ',8),'Perf City',$requirement?'pending':['pending','accepted','in_progress','completed'][$i%4],$i]);}
 $pdo->commit();echo "Seeded {$providers} providers and {$requests} service requests. Use --cleanup when finished.\n";
}catch(Throwable $e){if($pdo->inTransaction())$pdo->rollBack();throw $e;}
