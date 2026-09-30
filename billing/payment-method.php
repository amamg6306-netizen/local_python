<?php
declare(strict_types=1);
require_once __DIR__.'/../includes/auth.php';
require_once __DIR__.'/../includes/billing.php';
$user=require_role(['provider','business']);
$token=(string)($_GET['token']??'');$intent=checkout_intent($token,(int)$user['id']);
if(!$intent||$intent['status']!=='selecting_method'){flash('error','This checkout is unavailable or expired.');redirect(($user['role']==='business'?'business':'provider').'/subscription.php');}
if((string)$intent['user_role']!==(string)$user['role']){http_response_code(403);include __DIR__.'/../403.php';exit;}
$methods=configured_payment_methods_for_role((string)$user['role'],(string)$intent['currency']);
$pageTitle='Payment Method — LocalConnect';require __DIR__.'/../includes/header.php';
?>
<div class="container py-5" style="max-width:980px"><h1 class="fw-bold">Choose payment method</h1><p class="text-muted">Plan and price were verified and snapshotted on the server.</p>
<div class="row g-4"><div class="col-lg-5"><div class="card border-0 shadow-sm"><div class="card-body"><h2 class="h5"><?=e($intent['plan_name_snapshot'])?></h2><dl class="row small mb-0"><dt class="col-6">Subtotal</dt><dd class="col-6 text-end">₹<?=number_format((float)$intent['subtotal_amount'],2)?></dd><dt class="col-6">Tax</dt><dd class="col-6 text-end">₹<?=number_format((float)$intent['tax_amount'],2)?></dd><dt class="col-6">Billing period</dt><dd class="col-6 text-end"><?=(int)$intent['billing_period_months']?> month(s)</dd><dt class="col-6">Total</dt><dd class="col-6 text-end fw-bold">₹<?=number_format((float)$intent['total_amount'],2)?> <?=e($intent['currency'])?></dd></dl><hr><div class="small text-muted">Checkout expires at <?=e($intent['expires_at'])?>.</div></div></div></div>
<div class="col-lg-7"><?php if(!$methods):?><div class="alert alert-warning">No enabled, fully configured payment method is available for your role. Please contact the site administrator.</div><?php else:?><div class="vstack gap-3"><?php foreach($methods as $m):?><form method="post" action="<?=e(base_url('billing/select-method.php'))?>" class="card border-0 shadow-sm"><div class="card-body d-flex flex-wrap justify-content-between align-items-center gap-3"><?=csrf_field()?><input type="hidden" name="token" value="<?=e($token)?>"><input type="hidden" name="method_id" value="<?=(int)$m['id']?>"><div><h3 class="h5 mb-1"><?=e($m['name'])?></h3><div class="small text-muted"><?php if($m['method_type']==='gateway'):?>Secure hosted checkout; payment details are entered with the gateway, not LocalConnect.<?php elseif($m['method_type']==='upi'):?>Manual UPI transfer. Subscription stays pending until an admin verifies the transfer.<?php else:?>Manual bank transfer. Subscription stays pending until an admin verifies the transfer.<?php endif;?></div></div><button class="btn btn-primary">Continue</button></div></form><?php endforeach;?></div><?php endif;?></div></div></div>
<?php require __DIR__.'/../includes/footer.php';?>
