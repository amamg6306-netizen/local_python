<?php
declare(strict_types=1);
require_once __DIR__.'/../includes/auth.php';
$admin=require_role('admin');
$rows=db()->query("SELECT pm.*,cu.name created_by_name,uu.name updated_by_name FROM payment_methods pm JOIN users cu ON cu.id=pm.created_by JOIN users uu ON uu.id=pm.updated_by ORDER BY pm.display_order ASC,pm.id ASC")->fetchAll();
$audit=db()->query("SELECT a.*,u.name admin_name,pm.name method_name FROM payment_method_audit a JOIN users u ON u.id=a.admin_user_id JOIN payment_methods pm ON pm.id=a.payment_method_id ORDER BY a.id DESC LIMIT 50")->fetchAll();
$pageTitle='Payment Methods — Admin';
require __DIR__.'/../includes/header.php';
?>
<div class="container py-4">
<?php include __DIR__.'/_nav.php'; ?>
<div class="d-flex flex-wrap justify-content-between gap-3 align-items-center mb-3">
  <div><h1 class="mb-1">Payment methods</h1><p class="text-muted mb-0">Admin-managed options for provider/business subscriptions. Gateway secrets are never displayed or edited here.</p></div>
  <a class="btn btn-primary" href="<?=e(base_url('admin/payment-method-edit.php'))?>"><i class="fa-solid fa-plus me-1"></i>Add method</a>
</div>
<div class="alert alert-info"><strong>Phase 4:</strong> enabled methods can be used by provider/business checkout. Hosted gateway entitlement activates only after signed webhook verification plus server-side reconciliation; manual transfers require explicit admin reconciliation.</div>
<div class="card border-0 shadow-sm mb-4"><div class="table-responsive"><table class="table align-middle mb-0">
<thead><tr><th>Order</th><th>Method</th><th>Type</th><th>Audience</th><th>Currency</th><th>Configuration</th><th>Status</th><th></th></tr></thead><tbody>
<?php if(!$rows):?><tr><td colspan="8" class="text-center text-muted py-4">No payment methods configured.</td></tr><?php endif;?>
<?php foreach($rows as $r): $cfg=payment_method_configuration_status($r); ?>
<tr>
<td><?=number_format((int)$r['display_order'])?></td>
<td><strong><?=e($r['name'])?></strong><div class="small text-muted"><code><?=e($r['code'])?></code></div></td>
<td><?=e(str_replace('_',' ',ucfirst($r['method_type'])))?><?php if($r['gateway_code']):?><div class="small text-muted"><?=e($r['gateway_code'])?></div><?php endif;?></td>
<td><?=e(role_label($r['audience']==='both'?'provider':$r['audience']))?><?=$r['audience']==='both'?' + Business':''?></td>
<td><?=e($r['currency'])?></td>
<td><span class="badge text-bg-<?=$cfg['configured']?'success':'warning'?>"><?=e($cfg['summary'])?></span></td>
<td><span class="badge text-bg-<?=$r['is_active']?'success':'secondary'?>"><?=$r['is_active']?'Active':'Disabled'?></span></td>
<td><a class="btn btn-sm btn-outline-primary" href="<?=e(base_url('admin/payment-method-edit.php?id='.(int)$r['id']))?>">Edit</a></td>
</tr>
<?php endforeach;?></tbody></table></div></div>

<h2 class="h4">Recent method audit</h2>
<div class="card border-0 shadow-sm"><div class="table-responsive"><table class="table table-sm align-middle mb-0"><thead><tr><th>When</th><th>Admin</th><th>Method</th><th>Action</th></tr></thead><tbody>
<?php if(!$audit):?><tr><td colspan="4" class="text-muted text-center py-3">No changes recorded yet.</td></tr><?php endif;?>
<?php foreach($audit as $a):?><tr><td><?=e($a['created_at'])?></td><td><?=e($a['admin_name'])?></td><td><?=e($a['method_name'])?></td><td><code><?=e($a['action'])?></code></td></tr><?php endforeach;?>
</tbody></table></div></div>
</div>
<?php require __DIR__.'/../includes/footer.php'; ?>
