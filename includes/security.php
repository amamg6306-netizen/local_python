<?php
declare(strict_types=1);
require_once __DIR__ . '/../config/app.php';

/**
 * Browser/API response hardening for the production track.
 * CSP is nonce-based for LocalConnect's small amount of inline bootstrap data.
 */
function csp_nonce(): string
{
    static $nonce = null;
    if ($nonce === null) $nonce = base64_encode(random_bytes(18));
    return $nonce;
}

function hsts_header_value(): string
{
    $maxAge = max(300, min(63072000, env_int('HSTS_MAX_AGE', 31536000)));
    $value = 'max-age=' . $maxAge;
    if (env_bool('HSTS_INCLUDE_SUBDOMAINS', false)) $value .= '; includeSubDomains';
    if (env_bool('HSTS_PRELOAD', false)) $value .= '; preload';
    return $value;
}

function localconnect_csp(): string
{
    $nonce = csp_nonce();
    $directives = [
        "default-src 'self'",
        "base-uri 'self'",
        "object-src 'none'",
        "frame-ancestors 'none'",
        "form-action 'self'",
        "script-src 'self' 'nonce-{$nonce}' https://cdn.jsdelivr.net https://checkout.razorpay.com",
        "script-src-attr 'none'",
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com",
        "font-src 'self' data: https://cdnjs.cloudflare.com",
        "img-src 'self' data: blob: https://*.razorpay.com",
        "connect-src 'self' https://api.razorpay.com https://*.razorpay.com",
        "frame-src https://api.razorpay.com https://*.razorpay.com",
        "worker-src 'self' blob:",
        "manifest-src 'self'",
    ];
    if (is_production()) $directives[] = 'upgrade-insecure-requests';
    return implode('; ', $directives);
}

function apply_browser_security_headers(bool $authenticated = false): void
{
    if (headers_sent()) return;
    header_remove('X-Powered-By');
    header('X-Content-Type-Options: nosniff');
    header('X-Frame-Options: DENY');
    header('Referrer-Policy: strict-origin-when-cross-origin');
    header('Permissions-Policy: geolocation=(), camera=(), microphone=(), usb=(), interest-cohort=(), payment=(self "https://checkout.razorpay.com")');
    header('X-Permitted-Cross-Domain-Policies: none');
    if ($authenticated) header('Cache-Control: private, no-store, max-age=0');

    if (is_production() && request_is_https()) {
        header('Strict-Transport-Security: ' . hsts_header_value());
    }

    $mode = strtolower(env_value('SECURITY_CSP_MODE', is_production() ? 'enforce' : 'report-only') ?? 'report-only');
    $header = $mode === 'report-only' ? 'Content-Security-Policy-Report-Only' : 'Content-Security-Policy';
    header($header . ': ' . localconnect_csp());
}

function apply_api_security_headers(): void
{
    if (headers_sent()) return;
    header_remove('X-Powered-By');
    header('X-Content-Type-Options: nosniff');
    header('Cache-Control: no-store, max-age=0');
    header('Referrer-Policy: no-referrer');
    if (is_production() && request_is_https()) header('Strict-Transport-Security: ' . hsts_header_value());
}

function enforce_request_body_limit(int $maxBytes): void
{
    $length = $_SERVER['CONTENT_LENGTH'] ?? null;
    if ($length !== null && ctype_digit((string)$length) && (int)$length > $maxBytes) {
        http_response_code(413);
        exit('Request body is too large.');
    }
}
