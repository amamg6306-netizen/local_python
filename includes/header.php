<?php
require_once __DIR__ . '/auth.php';
require_once __DIR__ . '/security.php';
apply_browser_security_headers(is_logged_in());
$pageTitle = $pageTitle ?? 'LocalConnect';
$pageDescription = $pageDescription ?? 'Find trusted local professionals, workers and businesses near you.';
?>
<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="index,follow">
<title><?= e($pageTitle) ?></title><meta name="description" content="<?= e($pageDescription) ?>">
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
<link rel="stylesheet" href="<?= e(base_url('assets/css/style.css')) ?>">
</head><body>
<?php include __DIR__ . '/navbar.php'; ?>
<?php if ($msg = flash('success')): ?><div class="container mt-3"><div class="alert alert-success"><?= e($msg) ?></div></div><?php endif; ?>
<?php if ($msg = flash('error')): ?><div class="container mt-3"><div class="alert alert-danger"><?= e($msg) ?></div></div><?php endif; ?>
