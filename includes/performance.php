<?php
declare(strict_types=1);

/**
 * Lightweight request telemetry. No query strings, cookies, user IDs, request
 * bodies or secrets are logged. Disabled unless PERF_METRICS_ENABLED=true.
 */
function performance_metrics_enabled(): bool
{
    return env_bool('PERF_METRICS_ENABLED', false);
}

function performance_metrics_path(): string
{
    return __DIR__ . '/../storage/logs/performance.log';
}

function rotate_performance_log_if_needed(string $path): void
{
    $max = max(1_048_576, env_int('PERF_METRICS_MAX_BYTES', 10_485_760));
    clearstatcache(true, $path);
    if (is_file($path) && filesize($path) !== false && filesize($path) >= $max) {
        $backup = $path . '.1';
        if (is_file($backup)) @unlink($backup);
        @rename($path, $backup);
    }
}

function performance_register_request_metrics(): void
{
    if (!performance_metrics_enabled()) return;
    $started = hrtime(true);
    register_shutdown_function(static function () use ($started): void {
        $elapsedMs = (hrtime(true) - $started) / 1_000_000;
        $route = (string)($_SERVER['SCRIPT_NAME'] ?? 'cli');
        $method = strtoupper((string)($_SERVER['REQUEST_METHOD'] ?? 'CLI'));
        $entry = [
            'ts' => gmdate('c'),
            'route' => substr($route, 0, 240),
            'method' => preg_match('/^[A-Z]{2,10}$/', $method) ? $method : 'UNKNOWN',
            'status' => http_response_code(),
            'duration_ms' => round($elapsedMs, 3),
            'memory_peak_bytes' => memory_get_peak_usage(true),
            'memory_end_bytes' => memory_get_usage(true),
        ];
        $dir = dirname(performance_metrics_path());
        if (!is_dir($dir) && !@mkdir($dir, 0700, true) && !is_dir($dir)) return;
        $path = performance_metrics_path();
        rotate_performance_log_if_needed($path);
        $line = json_encode($entry, JSON_UNESCAPED_SLASHES) . PHP_EOL;
        if ($line !== false) @file_put_contents($path, $line, FILE_APPEND | LOCK_EX);
    });
}

performance_register_request_metrics();
