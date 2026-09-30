<?php
declare(strict_types=1);

if (session_status() !== PHP_SESSION_ACTIVE) {
    session_start();
}
require_once __DIR__ . '/../../includes/functions.php';

$failures = [];
$check = static function (bool $condition, string $message) use (&$failures): void {
    if (!$condition) {
        $failures[] = $message;
    }
};

$check(base_url('search.php') === '/localconnect/search.php', 'base_url should build the current application base path.');
$check(e('<script>') === '&lt;script&gt;', 'e() must HTML-escape angle brackets.');
$check(e('"\'&') === '&quot;&#039;&amp;', 'e() must HTML-escape quotes and ampersand.');
$check(slugify('AC & Cooling Service') === 'ac-cooling-service', 'slugify should normalize ordinary names.');
$check(slugify('   ') === 'item', 'slugify should return a safe fallback.');
$t1 = csrf_token();
$t2 = csrf_token();
$check(strlen($t1) === 64, 'CSRF token should be 32 random bytes encoded as 64 hex chars.');
$check(hash_equals($t1, $t2), 'CSRF token should remain stable during one session.');

if ($failures) {
    fwrite(STDERR, "FAIL\n - " . implode("\n - ", $failures) . "\n");
    exit(1);
}

echo "PASS: helper smoke tests (6 checks)\n";
