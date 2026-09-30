<?php
declare(strict_types=1);
require_once __DIR__.'/../includes/auth.php';
require_once __DIR__.'/../includes/billing.php';
$admin=require_role('admin');
$statuses=['pending','paid','failed','cancelled','refunded','partially_refunded','disputed','requires_review'];
$recons=['pending','matched','warning','manual_review'];
$status=in_array((string)($_GET['status']??''),$statuses,true)?(string)$_GET['status']:'';
$recon=in_array((string)($_GET['reconciliation']??''),$recons,true)?(string)$_GET['reconciliation']:'';
$qtext=trim((string)($_GET['q']??''));if(text_length($qtext)>120)$qtext=substr($qtext,0,120);
$page=max(1,(int)($_GET['page']??1));$per=25;$offset=($page-1)*$per;
$where=[];$params=[];
if($status!==''){$where[]='p.status=?';$params[]=$status;}
if($recon!==''){$where[]='p.reconciliation_status=?';$params[]=$recon;}
if($qtext!==''){$where[]='(u.email LIKE ? OR u.name LIKE ? OR p.provider_order_id LIKE ? OR p.provider_payment_id LIKE ? OR p.invoice_reference LIKE ?)';$like='%'.$qtext.'%';array_push($params,$like,$like,$like,$like,$like);}
$sqlWhere=$where?' WHERE '.implode(' AND ',$where):'';
$c=db()->prepare('SELECT COUNT(*) FROM payments p JOIN users u ON u.id=p.user_id'.$sqlWhere);$c->execute($params);$total=(int)$c->fetchColumn();
$sql='SELECT p.*,u.name,u.email,u.role,pm.name current_method_name FROM payments p JOIN users u ON u.id=p.user_id LEFT JOIN payment_methods pm ON pm.id=p.payment_method_id'.$sqlWhere.' ORDER BY p.id DESC LIMIT '.$per.' OFFSET '.$offset;
$q=db()->prepare($sql);$q->execute($params);$rows=$q->fetchAll();
$pageTitle='Payments — Admin';require __DIR__.'/../includes/header.php';
?>
<div class="container py-4"><?php include __DIR__.'/_nav.php';?><div class="d-flex flex-wrap justify-content-between gap-3 align-items-start"><div><h1>Payments</h1><p class="text-muted">Paginated immutable ledger with reconciliation state. Browser callbacks never mark a payment paid.</p></div><a class="btn btn-outline-secondary" href="<?=e(base_url('admin/payment-methods.php'))?>">Payment methods</a></div>
<form class="card border-0 shadow-sm mb-3" method="get"><div class="card-body row g-2"><div class="col-lg-4"><input class="form-control" name="q" value="<?=e($qtext)?>" placeholder="User, order, payment or invoice reference"></div><div class="col-md-3"><select class="form-select" name="status"><option value="">All payment statuses</option><?php foreach($statuses as $s):?><option value="<?=e($s)?>" <?=$status===$s?'selected':''?>><?=e($s)?></option><?php endforeach;?></select></div><div class="col-md-3"><select class="form-select" name="reconciliation"><option value="">All reconciliation states</option><?php foreach($recons as $s):?><option value="<?=e($s)?>" <?=$recon===$s?'selected':''?>><?=e($s)?></option><?php endforeach;?></select></div><div class="col-md-2"><button class="btn btn-primary w-100">Filter</button></div></div></form>
<div class="card border-0 shadow-sm"><div class="table-responsive"><table class="table align-middle mb-0"><thead><tr><th>ID</th><th>User</th><th>Plan</th><th>Method</th><th>Gateway refs</th><th>Amount</th><th>Status</th><th>Reconciliation</th><th>Created</th><th></th></tr></thead><tbody><?php if(!$rows):?><tr><td colspan="10" class="text-center text-muted py-4">No payments match the filters.</td></tr><?php endif;?><?php foreach($rows as $r):?><tr><td>#<?=(int)$r['id']?></td><td><?=e($r['name'])?><br><small><?=e($r['email'])?> · <?=e($r['role'])?></small></td><td><?=e($r['plan_name_snapshot']??'—')?></td><td><?=e($r['payment_method_name_snapshot']??$r['current_method_name']??'Legacy/unspecified')?></td><td class="small"><div><?=e($r['provider_order_id']??'—')?></div><div><?=e($r['provider_payment_id']??'—')?></div></td><td>₹<?=number_format((float)$r['amount'],2)?> <?=e($r['currency'])?></td><td><span class="badge text-bg-<?=$r['status']==='paid'?'success':(in_array($r['status'],['failed','cancelled','refunded','disputed'],true)?'danger':'warning')?>"><?=e($r['status'])?></span></td><td><?=e($r['reconciliation_status']??'—')?><?php if($r['reconciliation_note']):?><div class="small text-muted"><?=e($r['reconciliation_note'])?></div><?php endif;?></td><td><?=e($r['created_at'])?></td><td><a class="btn btn-sm btn-outline-primary" href="<?=e(base_url('admin/payment-detail.php?id='.(int)$r['id']))?>">Open</a></td></tr><?php endforeach;?></tbody></table></div></div>
<?php $pages=max(1,(int)ceil($total/$per));if($pages>1):?><nav class="mt-3"><ul class="pagination flex-wrap"><?php for($i=1;$i<=$pages;$i++):$query=http_build_query(['q'=>$qtext,'status'=>$status,'reconciliation'=>$recon,'page'=>$i]);?><li class="page-item <?=$i===$page?'active':''?>"><a class="page-link" href="?<?=e($query)?>"><?=$i?></a></li><?php endfor;?></ul></nav><?php endif;?></div>
<?php require __DIR__.'/../includes/footer.php';?>
