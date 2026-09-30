<?php
declare(strict_types=1);
require_once __DIR__.'/../includes/auth.php';
$admin=require_role('admin');
$statuses=['active','scheduled','expired','cancelled','pending','suspended'];
$status=in_array((string)($_GET['status']??''),$statuses,true)?(string)$_GET['status']:'';
$plan=trim((string)($_GET['plan']??''));if(text_length($plan)>40)$plan='';
$qtext=trim((string)($_GET['q']??''));if(text_length($qtext)>120)$qtext=substr($qtext,0,120);
$page=max(1,(int)($_GET['page']??1));$per=25;$offset=($page-1)*$per;
$where=[];$params=[];
if($status!==''){$where[]='s.status=?';$params[]=$status;}
if($plan!==''){$where[]='s.plan=?';$params[]=$plan;}
if($qtext!==''){$where[]='(u.email LIKE ? OR u.name LIKE ? OR s.invoice_reference LIKE ?)';$like='%'.$qtext.'%';array_push($params,$like,$like,$like);}
$ws=$where?' WHERE '.implode(' AND ',$where):'';
$c=db()->prepare('SELECT COUNT(*) FROM subscriptions s JOIN users u ON u.id=s.user_id'.$ws);$c->execute($params);$total=(int)$c->fetchColumn();
$sql='SELECT s.*,u.name,u.email,u.role FROM subscriptions s JOIN users u ON u.id=s.user_id'.$ws.' ORDER BY s.id DESC LIMIT '.$per.' OFFSET '.$offset;
$q=db()->prepare($sql);$q->execute($params);$rows=$q->fetchAll();
$plans=db()->query('SELECT code,name FROM subscription_plans ORDER BY price_monthly,id')->fetchAll();
$pageTitle='Subscriptions — Admin';require __DIR__.'/../includes/header.php';
?>
<div class="container py-4"><?php include __DIR__.'/_nav.php';?><h1>Subscriptions</h1><p class="text-muted">Paginated entitlement ledger, including scheduled renewals and suspended disputed entitlements.</p>
<form class="card border-0 shadow-sm mb-3" method="get"><div class="card-body row g-2"><div class="col-lg-4"><input class="form-control" name="q" value="<?=e($qtext)?>" placeholder="User or invoice reference"></div><div class="col-md-3"><select class="form-select" name="status"><option value="">All statuses</option><?php foreach($statuses as $s):?><option value="<?=e($s)?>" <?=$status===$s?'selected':''?>><?=e($s)?></option><?php endforeach;?></select></div><div class="col-md-3"><select class="form-select" name="plan"><option value="">All plans</option><?php foreach($plans as $p):?><option value="<?=e($p['code'])?>" <?=$plan===$p['code']?'selected':''?>><?=e($p['name'])?></option><?php endforeach;?></select></div><div class="col-md-2"><button class="btn btn-primary w-100">Filter</button></div></div></form>
<div class="card border-0 shadow-sm"><div class="table-responsive"><table class="table align-middle mb-0"><thead><tr><th>ID</th><th>User</th><th>Plan</th><th>Status</th><th>Price</th><th>Invoice</th><th>Period</th><th>Suspension</th></tr></thead><tbody><?php if(!$rows):?><tr><td colspan="8" class="text-center text-muted py-4">No subscriptions match the filters.</td></tr><?php endif;?><?php foreach($rows as $r):?><tr><td>#<?=(int)$r['id']?></td><td><?=e($r['name'])?><br><small><?=e($r['email'])?> · <?=e($r['role'])?></small></td><td><?=e(ucfirst($r['plan']))?></td><td><span class="badge text-bg-<?=$r['status']==='active'?'success':($r['status']==='suspended'?'danger':'secondary')?>"><?=e($r['status'])?></span></td><td>₹<?=number_format((float)$r['price'],2)?></td><td><?=e($r['invoice_reference']??'—')?></td><td><?=e($r['starts_at']??'—')?> → <?=e($r['ends_at']??'—')?></td><td><?=e($r['suspension_reason']??'—')?></td></tr><?php endforeach;?></tbody></table></div></div>
<?php $pages=max(1,(int)ceil($total/$per));if($pages>1):?><nav class="mt-3"><ul class="pagination flex-wrap"><?php for($i=1;$i<=$pages;$i++):$query=http_build_query(['q'=>$qtext,'status'=>$status,'plan'=>$plan,'page'=>$i]);?><li class="page-item <?=$i===$page?'active':''?>"><a class="page-link" href="?<?=e($query)?>"><?=$i?></a></li><?php endfor;?></ul></nav><?php endif;?></div>
<?php require __DIR__.'/../includes/footer.php';?>
