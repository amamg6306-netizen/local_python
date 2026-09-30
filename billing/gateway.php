<?php
declare(strict_types=1);
require_once __DIR__.'/../includes/auth.php';
require_once __DIR__.'/../includes/billing.php';
$user=require_role(['provider','business']);$token=(string)($_GET['token']??'');$intent=checkout_intent($token,(int)$user['id']);
if(!$intent||$intent['status']!=='pending_gateway'||empty($intent['payment_id'])){flash('error','Gateway checkout is unavailable.');redirect('billing/history.php');}
$payment=payment_by_id((int)$intent['payment_id']);if(!$payment||(int)$payment['user_id']!==(int)$user['id']){http_response_code(404);include __DIR__.'/../404.php';exit;}
try{$payment=create_razorpay_order((int)$payment['id']);$creds=razorpay_credentials();}catch(Throwable $e){flash('error',$e instanceof RuntimeException?$e->getMessage():'Gateway checkout could not be prepared.');redirect('billing/history.php');}
if(empty($payment['provider_order_id'])){flash('error','Gateway order is not ready.');redirect('billing/history.php');}
$pageTitle='Secure Checkout — LocalConnect';require __DIR__.'/../includes/header.php';
$checkout=[
 'key'=>$creds['key_id'],'amount'=>money_minor((string)$payment['amount']),'currency'=>(string)$payment['currency'],'name'=>'LocalConnect','description'=>(string)$payment['plan_name_snapshot'].' subscription','order_id'=>(string)$payment['provider_order_id'],
 'prefill'=>['name'=>(string)$user['name'],'email'=>(string)$user['email'],'contact'=>(string)($user['phone']??'')],
 'theme'=>['color'=>'#0d6efd']
];
?>
<div class="container py-5" style="max-width:760px"><div class="card border-0 shadow-sm"><div class="card-body p-4"><h1 class="h3">Secure hosted checkout</h1><p>Amount: <strong>₹<?=number_format((float)$payment['amount'],2)?> <?=e($payment['currency'])?></strong></p><div class="alert alert-info">Card/UPI/netbanking/wallet details are entered in Razorpay's hosted checkout. LocalConnect does not receive card numbers or CVV. A successful browser return does <strong>not</strong> activate the plan; activation waits for a signed webhook plus server-side reconciliation.</div><button id="payButton" class="btn btn-primary btn-lg">Open Razorpay Test Checkout</button><a class="btn btn-link" href="<?=e(base_url('billing/history.php'))?>">Back to billing history</a></div></div></div>
<form id="callbackForm" method="post" action="<?=e(base_url('billing/gateway-return.php'))?>" class="d-none"><?=csrf_field()?><input type="hidden" name="local_payment_id" value="<?=(int)$payment['id']?>"><input type="hidden" name="razorpay_payment_id" id="rpPayment"><input type="hidden" name="razorpay_order_id" id="rpOrder"><input type="hidden" name="razorpay_signature" id="rpSignature"></form>
<script nonce="<?=e(csp_nonce())?>" src="https://checkout.razorpay.com/v1/checkout.js"></script>
<script nonce="<?=e(csp_nonce())?>">
(function(){
 const options=<?=json_encode($checkout,JSON_UNESCAPED_SLASHES|JSON_HEX_TAG|JSON_HEX_AMP|JSON_HEX_APOS|JSON_HEX_QUOT)?>;
 options.handler=function(resp){document.getElementById('rpPayment').value=resp.razorpay_payment_id||'';document.getElementById('rpOrder').value=resp.razorpay_order_id||'';document.getElementById('rpSignature').value=resp.razorpay_signature||'';document.getElementById('callbackForm').submit();};
 options.modal={ondismiss:function(){window.location.href=<?=json_encode(base_url('billing/history.php'))?>;}};
 const rz=new Razorpay(options);document.getElementById('payButton').addEventListener('click',function(){rz.open();});
})();
</script>
<?php require __DIR__.'/../includes/footer.php';?>
