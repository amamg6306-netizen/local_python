<?php $pageTitle='Access denied — LocalConnect'; if(!defined('LC_403_INCLUDED')){define('LC_403_INCLUDED',true); require __DIR__.'/includes/header.php';} ?>
<div class="container py-5"><div class="soft-card p-5 text-center"><div class="display-3 mb-3">403</div><h2>You are not authorized to access this page.</h2><a class="btn btn-primary mt-3" href="<?=e(base_url())?>">Back to LocalConnect</a></div></div>
<?php require __DIR__.'/includes/footer.php'; ?>
