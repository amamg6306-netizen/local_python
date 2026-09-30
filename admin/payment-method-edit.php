<?php
declare(strict_types=1);
require_once __DIR__.'/../includes/auth.php';
$admin=require_admin_mfa_for_sensitive();
$id=max(0,(int)($_GET['id']??$_POST['id']??0));
$returnPath='admin/payment-method-edit.php'.($id>0?'?id='.$id:'');
require_recent_admin_reauth($returnPath,600);

$pdo=db();
$method=null;
if($id>0){$q=$pdo->prepare('SELECT * FROM payment_methods WHERE id=? LIMIT 1');$q->execute([$id]);$method=$q->fetch();if(!$method){http_response_code(404);include __DIR__.'/../404.php';exit;}}
$error='';

if($_SERVER['REQUEST_METHOD']==='POST'){
    verify_csrf();
    try{
        $name=clean_text($_POST['name']??'',120,true,'Method name');
        $type=clean_text($_POST['method_type']??'',30,true,'Method type');
        if(!in_array($type,['gateway','upi','bank_transfer'],true))throw new RuntimeException('Unsupported payment method type.');
        $audience=clean_text($_POST['audience']??'',20,true,'Audience');
        if(!in_array($audience,['provider','business','both'],true))throw new RuntimeException('Invalid audience.');
        $currency=normalize_currency($_POST['currency']??'INR');
        $order=(int)($_POST['display_order']??100);
        if($order<0||$order>10000)throw new RuntimeException('Display order must be between 0 and 10000.');
        $instructions=clean_text($_POST['display_instructions']??'',2000,false,'Display instructions');
        $gatewayCode=null;$upi=null;$beneficiary=null;$reference=null;
        if($type==='gateway'){
            $gatewayCode=clean_text($_POST['gateway_code']??'',60,true,'Gateway');
            if(!array_key_exists($gatewayCode,supported_payment_gateways()))throw new RuntimeException('Unsupported gateway.');
        }elseif($type==='upi'){
            $upi=clean_text($_POST['merchant_upi_id']??'',190,true,'Merchant UPI ID');
            if(!valid_upi_id($upi))throw new RuntimeException('Merchant UPI ID format is invalid.');
            if($instructions==='')throw new RuntimeException('UPI display instructions are required.');
        }else{
            $beneficiary=clean_text($_POST['bank_beneficiary']??'',160,true,'Bank beneficiary');
            $reference=clean_text($_POST['bank_reference']??'',190,false,'Bank reference');
            if($instructions==='')throw new RuntimeException('Bank transfer display instructions are required.');
        }
        $active=isset($_POST['is_active'])?1:0;
        $posted=['method_type'=>$type,'gateway_code'=>$gatewayCode,'merchant_upi_id'=>$upi,'bank_beneficiary'=>$beneficiary,'display_instructions'=>$instructions];
        $cfg=payment_method_configuration_status($posted);
        if($active && !$cfg['configured'])throw new RuntimeException('This method cannot be activated until its required configuration is complete.');

        $pdo->beginTransaction();
        if($method){
            $before=$method;
            $q=$pdo->prepare('UPDATE payment_methods SET name=?,method_type=?,gateway_code=?,audience=?,currency=?,merchant_upi_id=?,bank_beneficiary=?,bank_reference=?,display_instructions=?,display_order=?,is_active=?,updated_by=? WHERE id=?');
            $q->execute([$name,$type,$gatewayCode,$audience,$currency,$upi,$beneficiary,$reference?:null,$instructions?:null,$order,$active,(int)$admin['id'],$id]);
            $q=$pdo->prepare('SELECT * FROM payment_methods WHERE id=?');$q->execute([$id]);$after=$q->fetch();
            $action='update';
            if((int)$before['is_active']!==$active)$action=$active?'activate':'deactivate';
            elseif((int)$before['display_order']!==$order)$action='reorder';
            record_payment_method_audit($id,(int)$admin['id'],$action,$before,$after?:null);
            log_activity((int)$admin['id'],'payment_method_'.$action,'payment_method',$id,'code='.(string)$before['code']);
        }else{
            $code=clean_text($_POST['code']??'',60,true,'Method code');
            $code=slugify($code);
            if(!preg_match('/^[a-z0-9][a-z0-9-]{1,59}$/',$code))throw new RuntimeException('Method code must contain letters, numbers or hyphens.');
            $q=$pdo->prepare('INSERT INTO payment_methods(code,name,method_type,gateway_code,audience,currency,merchant_upi_id,bank_beneficiary,bank_reference,display_instructions,display_order,is_active,created_by,updated_by) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)');
            $q->execute([$code,$name,$type,$gatewayCode,$audience,$currency,$upi,$beneficiary,$reference?:null,$instructions?:null,$order,$active,(int)$admin['id'],(int)$admin['id']]);
            $id=(int)$pdo->lastInsertId();$q=$pdo->prepare('SELECT * FROM payment_methods WHERE id=?');$q->execute([$id]);$after=$q->fetch();
            record_payment_method_audit($id,(int)$admin['id'],'create',null,$after?:null);
            log_activity((int)$admin['id'],'payment_method_create','payment_method',$id,'code='.$code);
        }
        $pdo->commit();
        flash('success','Payment method saved.');redirect('admin/payment-methods.php');
    }catch(Throwable $e){if($pdo->inTransaction())$pdo->rollBack();$error=$e instanceof RuntimeException?$e->getMessage():'Payment method could not be saved.';security_log('payment_method_admin_error',['admin_id'=>(int)$admin['id'],'error_class'=>$e::class]);}
}

$form=$method?:['code'=>'','name'=>'','method_type'=>'gateway','gateway_code'=>'razorpay','audience'=>'both','currency'=>'INR','merchant_upi_id'=>'','bank_beneficiary'=>'','bank_reference'=>'','display_instructions'=>'','display_order'=>100,'is_active'=>0];
if($_SERVER['REQUEST_METHOD']==='POST')foreach(array_keys($form) as $k)if(array_key_exists($k,$_POST))$form[$k]=$_POST[$k];
$gatewayStatuses=[];foreach(supported_payment_gateways() as $code=>$g)$gatewayStatuses[$code]=payment_gateway_configuration_status($code);
$pageTitle=($method?'Edit':'Add').' Payment Method — Admin';require __DIR__.'/../includes/header.php';
?>
<div class="container py-4" style="max-width:980px"><?php include __DIR__.'/_nav.php';?>
<div class="d-flex justify-content-between align-items-start gap-3"><div><h1><?=$method?'Edit':'Add'?> payment method</h1><p class="text-muted">Sensitive changes require admin MFA and a recent password re-authentication.</p></div><a class="btn btn-outline-secondary" href="<?=e(base_url('admin/payment-methods.php'))?>">Back</a></div>
<?php if($error):?><div class="alert alert-danger"><?=e($error)?></div><?php endif;?>
<div class="alert alert-info"><strong>Secret handling:</strong> merchant API/webhook secrets are configured only in the server environment/secrets manager. This form never requests or displays them. Card numbers and CVV are never configured here.</div>
<form method="post" class="card border-0 shadow-sm"><div class="card-body p-4"><?=csrf_field()?><input type="hidden" name="id" value="<?=$id?>">
<div class="row g-3">
<div class="col-md-6"><label class="form-label">Method name</label><input class="form-control" name="name" maxlength="120" required value="<?=e((string)$form['name'])?>"></div>
<div class="col-md-6"><label class="form-label">Method code</label><?php if($method):?><input class="form-control" value="<?=e((string)$form['code'])?>" disabled><div class="form-text">Code is immutable after creation.</div><?php else:?><input class="form-control" name="code" maxlength="60" required pattern="[A-Za-z0-9-]+" value="<?=e((string)$form['code'])?>"><?php endif;?></div>
<div class="col-md-4"><label class="form-label">Type</label><select class="form-select" name="method_type" id="methodType"><option value="gateway" <?=$form['method_type']==='gateway'?'selected':''?>>Hosted gateway</option><option value="upi" <?=$form['method_type']==='upi'?'selected':''?>>Manual UPI</option><option value="bank_transfer" <?=$form['method_type']==='bank_transfer'?'selected':''?>>Manual bank transfer</option></select></div>
<div class="col-md-4"><label class="form-label">Audience</label><select class="form-select" name="audience"><option value="provider" <?=$form['audience']==='provider'?'selected':''?>>Provider</option><option value="business" <?=$form['audience']==='business'?'selected':''?>>Business</option><option value="both" <?=$form['audience']==='both'?'selected':''?>>Provider + Business</option></select></div>
<div class="col-md-2"><label class="form-label">Currency</label><select class="form-select" name="currency"><option value="INR">INR</option></select></div>
<div class="col-md-2"><label class="form-label">Order</label><input class="form-control" type="number" min="0" max="10000" name="display_order" value="<?=e((string)$form['display_order'])?>"></div>

<div class="col-12 method-section" data-types="gateway"><label class="form-label">Gateway</label><select class="form-select" name="gateway_code"><?php foreach(supported_payment_gateways() as $code=>$g):?><option value="<?=e($code)?>" <?=$form['gateway_code']===$code?'selected':''?>><?=e($g['label'])?></option><?php endforeach;?></select>
<div class="mt-2 small"><strong>Environment status:</strong><?php foreach($gatewayStatuses as $code=>$st):?><div class="mt-1"><span class="badge text-bg-<?=$st['configured']?'success':'warning'?>"><?=e($st['label'])?>: <?=$st['configured']?'configured':'incomplete'?></span><?php foreach($st['indicators'] as $env=>$state):?> <code><?=e($env)?></code>=<?=e($state)?><?php endforeach;?></div><?php endforeach;?></div></div>

<div class="col-md-6 method-section" data-types="upi"><label class="form-label">Merchant UPI ID</label><input class="form-control" name="merchant_upi_id" maxlength="190" value="<?=e((string)$form['merchant_upi_id'])?>" placeholder="merchant@bank"></div>
<div class="col-md-6 method-section" data-types="bank_transfer"><label class="form-label">Bank beneficiary</label><input class="form-control" name="bank_beneficiary" maxlength="160" value="<?=e((string)$form['bank_beneficiary'])?>"></div>
<div class="col-md-6 method-section" data-types="bank_transfer"><label class="form-label">Reference label/instruction</label><input class="form-control" name="bank_reference" maxlength="190" value="<?=e((string)$form['bank_reference'])?>" placeholder="Example: include payment reference in remarks"></div>
<div class="col-12 method-section" data-types="upi,bank_transfer,gateway"><label class="form-label">Display instructions</label><textarea class="form-control" name="display_instructions" maxlength="2000" rows="5"><?=e((string)$form['display_instructions'])?></textarea><div class="form-text">Plain text only. Do not paste API keys, webhook secrets, passwords, card data or arbitrary redirect URLs.</div></div>
<div class="col-12"><div class="form-check form-switch"><input class="form-check-input" type="checkbox" name="is_active" id="active" value="1" <?=(!empty($form['is_active']))?'checked':''?>><label class="form-check-label" for="active">Active for new checkout selections</label></div><div class="form-text">Disabling a method only blocks new selections. Existing pending payment records remain preserved for explicit reconciliation/cancellation.</div></div>
</div><button class="btn btn-primary mt-4">Save payment method</button></div></form>
</div>
<script nonce="<?=e(csp_nonce())?>"><!-- no secrets are present in this client-side script -->
(function(){const s=document.getElementById('methodType');function sync(){document.querySelectorAll('.method-section').forEach(x=>{const types=(x.dataset.types||'').split(',');x.style.display=types.includes(s.value)?'block':'none';});}s.addEventListener('change',sync);sync();})();
</script>
<?php require __DIR__.'/../includes/footer.php';?>
