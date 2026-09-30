<?php
declare(strict_types=1);

/**
 * Runtime configuration helpers. Production secrets must be supplied by the
 * process environment (Apache/FPM/systemd/container/secret manager). The app
 * intentionally does not auto-load a web-root .env file.
 */
function env_value(string $key, ?string $default = null): ?string
{
    $value = getenv($key);
    if ($value === false && array_key_exists($key, $_ENV)) {
        $value = (string)$_ENV[$key];
    }
    if ($value === false || $value === '') return $default;
    return (string)$value;
}

function env_bool(string $key, bool $default = false): bool
{
    $value = env_value($key);
    if ($value === null) return $default;
    $parsed = filter_var($value, FILTER_VALIDATE_BOOL, FILTER_NULL_ON_FAILURE);
    return $parsed ?? $default;
}

function env_int(string $key, int $default): int
{
    $value = env_value($key);
    return $value !== null && preg_match('/^-?\d+$/', $value) ? (int)$value : $default;
}

function app_env(): string { return strtolower(env_value('APP_ENV', 'development') ?? 'development'); }
function is_production(): bool { return app_env() === 'production'; }
function app_debug(): bool { return env_bool('APP_DEBUG', !is_production()); }

function request_from_trusted_proxy(): bool
{
    if (!env_bool('TRUST_PROXY', false)) return false;
    $remote = $_SERVER['REMOTE_ADDR'] ?? '';
    $raw = env_value('TRUSTED_PROXY_IPS', '') ?? '';
    $trusted = array_values(array_filter(array_map('trim', explode(',', $raw))));
    return $remote !== '' && in_array($remote, $trusted, true);
}

function request_is_https(): bool
{
    if (!empty($_SERVER['HTTPS']) && strtolower((string)$_SERVER['HTTPS']) !== 'off') return true;
    if (request_from_trusted_proxy()) {
        $proto = strtolower(trim(explode(',', (string)($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? ''))[0]));
        return $proto === 'https';
    }
    return false;
}

function configured_base_path(): string
{
    $path = trim(env_value('APP_BASE_PATH', '/localconnect/') ?? '/localconnect/');
    if ($path === '') return '/';
    $trimmed = trim($path, '/');
    if ($trimmed === '') return '/';
    return '/' . $trimmed . '/';
}

function app_origin(): string
{
    $configured = rtrim(env_value('APP_URL', '') ?? '', '/');
    if ($configured !== '') return $configured;
    if (is_production()) return '';
    $scheme = request_is_https() ? 'https' : 'http';
    $host = preg_replace('/[^A-Za-z0-9.\-:\[\]]/', '', (string)($_SERVER['HTTP_HOST'] ?? 'localhost')) ?: 'localhost';
    return $scheme . '://' . $host . rtrim(configured_base_path(), '/');
}

function app_key_bytes(bool $required = false): string
{
    $raw = env_value('APP_KEY', '') ?? '';
    if (str_starts_with($raw, 'base64:')) {
        $decoded = base64_decode(substr($raw, 7), true);
        if ($decoded !== false && strlen($decoded) >= 32) return substr($decoded, 0, 32);
    } elseif (str_starts_with($raw, 'hex:')) {
        $decoded = hex2bin(substr($raw, 4));
        if ($decoded !== false && strlen($decoded) >= 32) return substr($decoded, 0, 32);
    } elseif (strlen($raw) >= 32) {
        return hash('sha256', $raw, true);
    }
    if ($required || is_production()) {
        throw new RuntimeException('APP_KEY is missing or invalid. Configure a 32-byte-or-stronger application key.');
    }
    // Development-only deterministic key. Never considered production-safe.
    return hash('sha256', __DIR__ . '|localconnect-development-only', true);
}

function app_hmac(string $value, string $purpose): string
{
    return hash_hmac('sha256', $purpose . "\0" . $value, app_key_bytes(is_production()));
}



function configure_runtime_error_policy(): void
{
    if (PHP_SAPI === 'cli') return;
    if (is_production()) {
        @ini_set('display_errors', '0');
        @ini_set('display_startup_errors', '0');
        @ini_set('log_errors', '1');
    }
    if (!headers_sent()) header_remove('X-Powered-By');
}

function enforce_production_https(): void
{
    if (PHP_SAPI === 'cli' || !is_production() || !env_bool('FORCE_HTTPS', true) || request_is_https()) return;
    $configured = env_value('APP_URL', '') ?? '';
    $parts = parse_url($configured);
    if (!is_array($parts) || strtolower((string)($parts['scheme'] ?? '')) !== 'https' || empty($parts['host'])) {
        http_response_code(503);
        exit('Production HTTPS configuration is incomplete.');
    }
    $origin = 'https://' . $parts['host'] . (isset($parts['port']) ? ':' . (int)$parts['port'] : '');
    $uri = (string)($_SERVER['REQUEST_URI'] ?? configured_base_path());
    if ($uri === '' || !str_starts_with($uri, '/')) $uri = configured_base_path();
    if (preg_match('/[\\r\\n]/', $uri)) $uri = configured_base_path();
    header('Location: ' . $origin . $uri, true, 308);
    exit;
}

function production_config_errors(): array
{
    if (!is_production()) return [];
    $errors = [];
    $appUrl = env_value('APP_URL', '') ?? '';
    if ($appUrl === '') $errors[] = 'APP_URL is required in production.';
    elseif (!preg_match('#^https://#i', $appUrl)) $errors[] = 'APP_URL must use https:// in production.';
    try { app_key_bytes(true); } catch (Throwable $e) { $errors[] = $e->getMessage(); }
    if ((env_value('DB_HOST', '') ?? '') === '') $errors[] = 'DB_HOST is required in production.';
    if ((env_value('DB_NAME', '') ?? '') === '') $errors[] = 'DB_NAME is required in production.';
    $dbUser = env_value('DB_USER', '') ?? '';
    if ($dbUser === '' || strtolower($dbUser) === 'root') $errors[] = 'Use a dedicated least-privilege DB_USER in production.';
    $dbPass = env_value('DB_PASS', '') ?? '';
    if ($dbPass === '') $errors[] = 'DB_PASS must not be blank in production.';
    elseif (str_contains($dbPass, 'REPLACE_WITH_')) $errors[] = 'DB_PASS still contains a placeholder value.';
    if (!env_bool('SESSION_COOKIE_SECURE', true)) $errors[] = 'SESSION_COOKIE_SECURE must be enabled in production.';
    if (app_debug()) $errors[] = 'APP_DEBUG must be disabled in production.';
    if (!env_bool('FORCE_HTTPS', true)) $errors[] = 'FORCE_HTTPS must be enabled in production.';
    if (!env_bool('APP_ADMIN_MFA_REQUIRED', true)) $errors[] = 'APP_ADMIN_MFA_REQUIRED must be enabled in production.';
    if (!env_bool('APP_REQUIRE_EMAIL_VERIFICATION', true)) $errors[] = 'APP_REQUIRE_EMAIL_VERIFICATION must be enabled in production.';
    if (!env_bool('UPLOAD_REQUIRE_REENCODE', true)) $errors[] = 'UPLOAD_REQUIRE_REENCODE must be enabled in production.';
    if (env_bool('TRUST_PROXY', false) && trim(env_value('TRUSTED_PROXY_IPS', '') ?? '') === '') $errors[] = 'TRUSTED_PROXY_IPS is required when TRUST_PROXY is enabled.';
    $cspMode = strtolower(env_value('SECURITY_CSP_MODE', 'enforce') ?? 'enforce');
    if ($cspMode !== 'enforce') $errors[] = 'SECURITY_CSP_MODE must be enforce in production.';
    if (env_int('HSTS_MAX_AGE', 31536000) < 31536000) $errors[] = 'HSTS_MAX_AGE should be at least 31536000 seconds in production.';
    return array_values(array_unique($errors));
}

configure_runtime_error_policy();
