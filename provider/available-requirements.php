<?php
require_once __DIR__.'/../includes/auth.php';
$u=require_role(['provider','business']);
$pg=pagination_window(20,40);release_session_lock();
$sql="SELECT r.id,r.customer_id,r.category_id,r.service_id,r.title,r.description,r.location_text,r.preferred_date,r.preferred_time,r.budget_min,r.budget_max,r.status,r.created_at,cu.name customer_name,c.name category_name,s.name service_name
FROM service_requests r
JOIN users cu ON cu.id=r.customer_id
JOIN categories c ON c.id=r.category_id
LEFT JOIN services s ON s.id=r.service_id
WHERE r.request_type='requirement' AND r.status='pending' AND r.provider_id IS NULL AND r.business_id IS NULL
AND EXISTS(SELECT 1 FROM provider_services ps WHERE ps.provider_user_id=? AND ps.service_id=r.service_id AND ps.is_active=1)
ORDER BY r.created_at DESC,r.id DESC LIMIT ".($pg['per']+1)." OFFSET ".$pg['offset'];
$q=db()->prepare($sql);$q->execute([(int)$u['id']]);$rows=$q->fetchAll();$hasNext=trim_page_results($rows,$pg['per']);
$pageTitle='Available Requirements — LocalConnect';require __DIR__.'/../includes/header.php';?>
<div class="container py-5"><h1 class="fw-bold">Available Requirements</h1><p class="text-muted">Open requirements matching services you offer.</p>
<?php if(!$rows):?><div class="soft-card text-center p-5"><h3>No matching requirements right now.</h3><p class="text-muted mb-0">Make sure your service list is complete. Matching open requests will appear here.</p></div>
<?php else:?><?php foreach($rows as $r):?><div class="soft-card p-4 mb-3"><div class="small text-muted"><?=e($r['service_name']?:$r['category_name'])?> · <?=e($r['location_text'])?></div><h3 class="h5 mt-1"><?=e($r['title'])?></h3><p class="mb-2"><?=e($r['description'])?></p><div class="small text-muted">Budget: <?=($r['budget_min']!==null?'₹'.number_format((float)$r['budget_min']):'Not specified')?><?=($r['budget_max']!==null?' – ₹'.number_format((float)$r['budget_max']):'')?></div><a class="btn btn-primary btn-sm mt-3" href="<?=e(base_url('request-details.php?id='.$r['id']))?>">View Requirement</a></div><?php endforeach;?><?=pagination_nav($pg['page'],$hasNext)?><?php endif;?></div>
<?php require __DIR__.'/../includes/footer.php';?>
