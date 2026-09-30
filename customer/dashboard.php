<?php
require_once __DIR__.'/../includes/auth.php';
$user=require_role('customer');
$pageTitle=role_label($user['role']).' Dashboard — LocalConnect'; require __DIR__.'/../includes/header.php';
?>
<div class="container py-5 dashboard-shell"><div class="d-flex flex-wrap justify-content-between align-items-center gap-3 mb-4"><div><span class="badge badge-soft rounded-pill mb-2"><?=e(role_label($user['role']))?></span><h1 class="fw-bold mb-1">Welcome, <?=e($user['name'])?></h1><p class="text-muted mb-0">Find services, manage requests and keep track of your LocalConnect activity.</p></div></div><div class="row g-4"><div class="col-md-4"><div class="soft-card p-4 h-100"><h5>Account</h5><p class="text-muted mb-1"><?=e($user['email'])?></p><p class="mb-0"><?=e(trim(($user['city']??'').' '.($user['state']??'')) ?: 'Location not set')?></p></div></div><div class="col-md-8"><div class="soft-card p-4 h-100"><h5>Quick actions</h5><div class="d-flex flex-wrap gap-2"><a class="btn btn-primary" href="<?=e(base_url('search.php'))?>">Search Services</a><a class="btn btn-outline-primary" href="<?=e(base_url('post-requirement.php'))?>">Post a Requirement</a><a class="btn btn-outline-secondary" href="<?=e(base_url('customer/requests.php'))?>">My Requests</a></div></div></div></div></div>
<?php require __DIR__.'/../includes/footer.php'; ?>
