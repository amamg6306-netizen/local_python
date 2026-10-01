<?php
declare(strict_types=1);
require_once __DIR__ . '/app.php';
enforce_production_https();

function db_config(): array
{
    $prod = is_production();
    return [
        'host' => env_value('DB_HOST', $prod ? null : 'dpg-daukqqh7lnhs738uu400-a'),
        'port' => env_value('DB_PORT', '3306'),
        'name' => env_value('DB_NAME', $prod ? null : 'python_db_0dgf'),
        'user' => env_value('DB_USER', $prod ? null : 'python_db_0dgf_user'),
        'pass' => env_value('DB_PASS', $prod ? null : 'hUtvSorRgbIEniNHha9OSAMMKrD7wNMN'),
    ];
}

function db(): PDO
{
    static $pdo = null;
    if ($pdo instanceof PDO) return $pdo;

    try {
        if (is_production()) {
            $errors = production_config_errors();
            if ($errors) throw new RuntimeException('Production configuration is incomplete.');
        }
        $cfg = db_config();
        foreach (['host','name','user'] as $required) {
            if (!is_string($cfg[$required]) || $cfg[$required] === '') throw new RuntimeException('Database configuration is incomplete.');
        }
        $dsn = 'mysql:host=' . $cfg['host'] . ';port=' . ($cfg['port'] ?: '3306') . ';dbname=' . $cfg['name'] . ';charset=utf8mb4';
        $pdo = new PDO($dsn, (string)$cfg['user'], (string)$cfg['pass'], [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
            PDO::ATTR_STRINGIFY_FETCHES => false,
        ]);
        return $pdo;
    } catch (Throwable $e) {
        error_log('[LocalConnect][database] connection failed: ' . $e::class . ' code=' . $e->getCode());
        http_response_code(500);
        $message = is_production()
            ? 'LocalConnect is temporarily unavailable. Please try again later.'
            : 'LocalConnect could not connect to the database. Check environment variables and import the development database.';
        exit($message);
    }
}
