<?php
declare(strict_types=1);
require_once __DIR__ . '/../config/app.php';

function base_url(string $path = ''): string
{
    return configured_base_path() . ltrim($path, '/');
}

function absolute_url(string $path = ''): string
{
    $origin = app_origin();
    if ($origin === '') throw new RuntimeException('APP_URL must be configured before generating absolute links.');
    return rtrim($origin, '/') . '/' . ltrim($path, '/');
}

function e(?string $value): string
{
    return htmlspecialchars((string)$value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function redirect(string $path): never
{
    if (preg_match('#^[a-z][a-z0-9+.-]*://#i', $path) || str_contains($path, "\r") || str_contains($path, "\n")) {
        $path = 'index.php';
    }
    header('Location: ' . base_url($path), true, 303);
    exit;
}

function safe_admin_return(string $path, string $fallback = 'admin/index.php'): string
{
    $path = ltrim(trim($path), '/');
    if ($path === '' || !str_starts_with($path, 'admin/') || str_contains($path, '..') || str_contains($path, '\\') || str_contains($path, '://')) return $fallback;
    return $path;
}

function csrf_token(): string
{
    if (empty($_SESSION['csrf_token'])) $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
    return $_SESSION['csrf_token'];
}

function csrf_field(): string
{
    return '<input type="hidden" name="csrf_token" value="' . e(csrf_token()) . '">';
}

function verify_csrf(): void
{
    $token = (string)($_POST['csrf_token'] ?? '');
    if ($token === '' || !hash_equals((string)($_SESSION['csrf_token'] ?? ''), $token)) {
        http_response_code(419);
        exit('Your session token is invalid or expired. Please reload the page and try again.');
    }
}

function flash(string $key, ?string $message = null): ?string
{
    if ($message !== null) { $_SESSION['flash'][$key] = $message; return null; }
    $value = $_SESSION['flash'][$key] ?? null;
    unset($_SESSION['flash'][$key]);
    return is_string($value) ? $value : null;
}

function text_length(string $value): int
{
    if (function_exists('mb_strlen')) return mb_strlen($value, 'UTF-8');
    $ok = preg_match_all('/./us', $value, $m);
    return $ok === false ? strlen($value) : $ok;
}

function clean_text(mixed $value, int $max, bool $required = false, string $label = 'Field'): string
{
    $text = trim(is_string($value) ? $value : '');
    if ($required && $text === '') throw new RuntimeException($label . ' is required.');
    if (text_length($text) > $max) throw new RuntimeException($label . ' is too long.');
    if (str_contains($text, "\0")) throw new RuntimeException($label . ' contains invalid characters.');
    return $text;
}

function nullable_money(mixed $value, string $label = 'Amount', float $max = 100000000.0): ?float
{
    if ($value === '' || $value === null) return null;
    if (!is_numeric($value)) throw new RuntimeException($label . ' must be a number.');
    $number = (float)$value;
    if (!is_finite($number) || $number < 0 || $number > $max) throw new RuntimeException($label . ' is outside the allowed range.');
    return round($number, 2);
}

function valid_phone_or_empty(string $phone): bool
{
    return $phone === '' || (bool)preg_match('/^[0-9+() .-]{7,25}$/', $phone);
}

function valid_pincode_or_empty(string $value): bool
{
    return $value === '' || (bool)preg_match('/^[A-Za-z0-9 -]{3,12}$/', $value);
}

function validated_http_url(mixed $value, int $max = 255): ?string
{
    $url = clean_text($value, $max, false, 'URL');
    if ($url === '') return null;
    if (!filter_var($url, FILTER_VALIDATE_URL)) throw new RuntimeException('Please enter a valid URL.');
    $parts = parse_url($url);
    $scheme = strtolower((string)($parts['scheme'] ?? ''));
    if (!in_array($scheme, ['https','http'], true) || empty($parts['host'])) throw new RuntimeException('Only http:// or https:// URLs are allowed.');
    if (isset($parts['user']) || isset($parts['pass'])) throw new RuntimeException('URLs with embedded credentials are not allowed.');
    return $url;
}

function nullable_date(mixed $value, bool $allowPast = true, string $label = 'Date'): ?string
{
    $raw = trim(is_string($value) ? $value : '');
    if ($raw === '') return null;
    $dt = DateTimeImmutable::createFromFormat('!Y-m-d', $raw);
    $errors = DateTimeImmutable::getLastErrors();
    if (!$dt || ($errors !== false && (($errors['warning_count'] ?? 0) || ($errors['error_count'] ?? 0))) || $dt->format('Y-m-d') !== $raw) throw new RuntimeException($label . ' is invalid.');
    if (!$allowPast && $dt < new DateTimeImmutable('today')) throw new RuntimeException($label . ' cannot be in the past.');
    return $raw;
}

function nullable_time(mixed $value, string $label = 'Time'): ?string
{
    $raw = trim(is_string($value) ? $value : '');
    if ($raw === '') return null;
    if (!preg_match('/^(?:[01]\d|2[0-3]):[0-5]\d$/', $raw)) throw new RuntimeException($label . ' is invalid.');
    return $raw . ':00';
}

function nullable_datetime_local(mixed $value, string $label = 'Date/time'): ?string
{
    $raw = trim(is_string($value) ? $value : '');
    if ($raw === '') return null;
    $dt = DateTimeImmutable::createFromFormat('!Y-m-d\\TH:i', $raw);
    $errors = DateTimeImmutable::getLastErrors();
    if (!$dt || ($errors !== false && (($errors['warning_count'] ?? 0) || ($errors['error_count'] ?? 0)))) throw new RuntimeException($label . ' is invalid.');
    return $dt->format('Y-m-d H:i:s');
}

function safe_local_path(?string $path, string $fallback = ''): string
{
    $path = ltrim(trim((string)$path), '/');
    if ($path === '' || str_contains($path, '..') || str_contains($path, '\\') || str_contains($path, '://') || preg_match('/[\r\n]/', $path)) return $fallback;
    return $path;
}

function pagination_window(int $defaultPer = 20, int $maxPer = 50): array
{
    $maxPage = max(10, min(10000, env_int('PAGINATION_MAX_PAGE', 1000)));
    $pageRaw = filter_input(INPUT_GET, 'page', FILTER_VALIDATE_INT, ['options'=>['min_range'=>1]]);
    $perRaw = filter_input(INPUT_GET, 'per_page', FILTER_VALIDATE_INT, ['options'=>['min_range'=>1]]);
    $page = $pageRaw ?: 1;
    $per = $perRaw ?: $defaultPer;
    $page = max(1, min($maxPage, (int)$page));
    $per = max(1, min($maxPer, (int)$per));
    return ['page'=>$page, 'per'=>$per, 'offset'=>($page-1)*$per, 'max_page'=>$maxPage];
}

function trim_page_results(array &$rows, int $per): bool
{
    if (count($rows) <= $per) return false;
    array_pop($rows);
    return true;
}

function pagination_href(int $page): string
{
    $query = $_GET;
    unset($query['csrf_token']);
    $query['page'] = max(1, $page);
    return '?' . http_build_query($query, '', '&', PHP_QUERY_RFC3986);
}

function pagination_nav(int $page, bool $hasNext): string
{
    if ($page <= 1 && !$hasNext) return '';
    $html = '<nav class="d-flex justify-content-between align-items-center mt-4" aria-label="Pagination">';
    $html .= $page > 1
        ? '<a class="btn btn-outline-secondary" rel="prev" href="' . e(pagination_href($page - 1)) . '">&larr; Newer</a>'
        : '<span></span>';
    $html .= '<span class="text-muted small">Page ' . $page . '</span>';
    $html .= $hasNext
        ? '<a class="btn btn-outline-secondary" rel="next" href="' . e(pagination_href($page + 1)) . '">Older &rarr;</a>'
        : '<span></span>';
    return $html . '</nav>';
}

function release_session_lock(): void
{
    if (session_status() === PHP_SESSION_ACTIVE) {
        // Ensure the navbar/state-changing forms keep a persisted token even when
        // long read-only database/render work no longer holds the session lock.
        csrf_token();
        session_write_close();
    }
}

function role_label(string $role): string
{
    return match ($role) {
        'customer' => 'Customer', 'provider' => 'Service Provider', 'business' => 'Business Owner', 'admin' => 'Administrator', default => ucfirst($role),
    };
}

function dashboard_for(string $role): string
{
    return match ($role) {
        'customer' => 'customer/dashboard.php', 'provider' => 'provider/dashboard.php', 'business' => 'business/dashboard.php', 'admin' => 'admin/index.php', default => 'index.php',
    };
}

function slugify(string $text): string
{
    $text = strtolower(trim($text));
    $text = preg_replace('/[^a-z0-9]+/i', '-', $text) ?? '';
    return trim($text, '-') ?: 'item';
}

function ini_size_bytes(string $value): int
{
    $value=trim($value);if($value===''||$value==='-1')return -1;
    $unit=strtolower(substr($value,-1));$number=(float)$value;
    return match($unit){'g'=>(int)($number*1073741824),'m'=>(int)($number*1048576),'k'=>(int)($number*1024),default=>(int)$number};
}

function image_decode_fits_memory(int $width,int $height,int $encodedBytes): bool
{
    $limit=ini_size_bytes((string)ini_get('memory_limit'));if($limit<0)return true;
    // Conservative GD working-set estimate: decoded RGBA + row/allocator overhead,
    // encoded input and an 8 MiB application safety allowance.
    $estimate=($width*$height*5)+($encodedBytes*2)+8_388_608;
    $budget=(int)floor($limit*0.80);
    return memory_get_usage(true)+$estimate <= $budget;
}

function upload_image(array $file, string $folder, int $maxBytes = 3145728): ?string
{
    if (($file['error'] ?? UPLOAD_ERR_NO_FILE) === UPLOAD_ERR_NO_FILE) return null;
    if (($file['error'] ?? UPLOAD_ERR_OK) !== UPLOAD_ERR_OK) throw new RuntimeException('Image upload failed.');
    $tmp = (string)($file['tmp_name'] ?? '');
    if ($tmp === '' || !is_uploaded_file($tmp)) throw new RuntimeException('Invalid uploaded file.');
    $size = (int)($file['size'] ?? 0);
    if ($size <= 0 || $size > $maxBytes) throw new RuntimeException('Image must be between 1 byte and 3 MB.');

    $allowedFolders = ['profiles','businesses','portfolio'];
    if (!in_array($folder, $allowedFolders, true)) throw new RuntimeException('Invalid upload destination.');

    $info = @getimagesize($tmp);
    if ($info === false) throw new RuntimeException('The uploaded file is not a valid image.');
    $width = (int)($info[0] ?? 0); $height = (int)($info[1] ?? 0);
    $maxDimension = max(256, env_int('UPLOAD_MAX_DIMENSION', 6000));
    $maxPixels = max(1_000_000, env_int('UPLOAD_MAX_PIXELS', 20_000_000));
    if ($width < 1 || $height < 1 || $width > $maxDimension || $height > $maxDimension || ($width * $height) > $maxPixels) {
        throw new RuntimeException('Image dimensions are too large.');
    }

    $finfo = new finfo(FILEINFO_MIME_TYPE);
    $mime = (string)$finfo->file($tmp);
    $allowed = ['image/jpeg'=>'jpg','image/png'=>'png','image/webp'=>'webp'];
    if (!isset($allowed[$mime])) throw new RuntimeException('Only JPG, PNG and WEBP images are allowed.');
    if (($info['mime'] ?? '') !== $mime) throw new RuntimeException('Image format validation failed.');

    $dir = __DIR__ . '/../uploads/' . $folder;
    if (!is_dir($dir) && !mkdir($dir, 0755, true) && !is_dir($dir)) throw new RuntimeException('Upload storage is unavailable.');
    $name = bin2hex(random_bytes(16)) . '.' . $allowed[$mime];
    $destination = $dir . '/' . $name;

    $reencoded = false;
    if (!image_decode_fits_memory($width,$height,$size)) throw new RuntimeException('Image is too large to process safely on this server.');
    $decoder = match($mime) {
        'image/jpeg' => function_exists('imagecreatefromjpeg') ? 'imagecreatefromjpeg' : null,
        'image/png' => function_exists('imagecreatefrompng') ? 'imagecreatefrompng' : null,
        'image/webp' => function_exists('imagecreatefromwebp') ? 'imagecreatefromwebp' : null,
        default => null,
    };
    if ($decoder !== null) {
        $image = @$decoder($tmp);
        if ($image === false) throw new RuntimeException('Image decoding failed.');
        if ($mime === 'image/jpeg' && function_exists('imagejpeg')) $reencoded = imagejpeg($image, $destination, 88);
        elseif ($mime === 'image/png' && function_exists('imagepng')) $reencoded = imagepng($image, $destination, 6);
        elseif ($mime === 'image/webp' && function_exists('imagewebp')) $reencoded = imagewebp($image, $destination, 88);
        imagedestroy($image);
    }

    if (!$reencoded) {
        if (is_production() && env_bool('UPLOAD_REQUIRE_REENCODE', true)) {
            throw new RuntimeException('Secure image re-encoding is unavailable on this server. Enable the PHP GD extension.');
        }
        if (!move_uploaded_file($tmp, $destination)) throw new RuntimeException('Could not save uploaded image.');
    }
    @chmod($destination, 0644);
    return 'uploads/' . $folder . '/' . $name;
}

function delete_managed_upload(?string $path): void
{
    if (!$path || !preg_match('#^uploads/(profiles|businesses|portfolio)/[a-f0-9]{32}\.(jpg|png|webp)$#', $path)) return;
    $full = realpath(__DIR__ . '/../' . $path);
    $uploads = realpath(__DIR__ . '/../uploads');
    if ($full && $uploads && str_starts_with($full, $uploads . DIRECTORY_SEPARATOR) && is_file($full)) @unlink($full);
}

function rating_summary(int $userId): array
{
    $s=db()->prepare("SELECT COALESCE(AVG(rating),0) avg_rating, COUNT(*) total FROM reviews WHERE target_user_id=? AND status='published'");
    $s->execute([$userId]); return $s->fetch() ?: ['avg_rating'=>0,'total'=>0];
}
function is_favorite(int $customerId, int $targetUserId): bool
{
    $s=db()->prepare('SELECT 1 FROM favorites WHERE customer_id=? AND target_user_id=? LIMIT 1');
    $s->execute([$customerId,$targetUserId]); return (bool)$s->fetchColumn();
}
function unread_notification_count(int $userId): int
{
    $s=db()->prepare('SELECT COUNT(*) FROM notifications WHERE user_id=? AND is_read=0');
    $s->execute([$userId]); return (int)$s->fetchColumn();
}

function redact_log_scalar(mixed $value): mixed
{
    if (!is_string($value)) return $value;
    $value = preg_replace('/rzp_(?:live|test)_[A-Za-z0-9_-]+/i', '[REDACTED_RAZORPAY_KEY]', $value) ?? '[REDACTED]';
    $value = preg_replace('/\bBearer\s+[A-Za-z0-9._~+\/-]+=*/i', 'Bearer [REDACTED]', $value) ?? '[REDACTED]';
    $value = preg_replace('/(?i)(secret|password|token|authorization|cookie)\s*[=:]\s*[^\s,;]+/', '$1=[REDACTED]', $value) ?? '[REDACTED]';
    return substr($value, 0, 500);
}

function security_log(string $event, array $context = []): void
{
    $safe = [];
    foreach ($context as $key => $value) {
        if (preg_match('/pass|secret|token|authorization|cookie/i', (string)$key)) continue;
        if (is_scalar($value) || $value === null) $safe[(string)$key] = redact_log_scalar($value);
    }
    error_log('[LocalConnect][security] ' . preg_replace('/[^a-z0-9_.-]/i','_',substr($event,0,120)) . ' ' . json_encode($safe, JSON_UNESCAPED_SLASHES));
}

function log_activity(?int $actorId, string $action, ?string $targetType=null, ?int $targetId=null, ?string $details=null): void
{
    try {
        $q=db()->prepare('INSERT INTO platform_activity(actor_id,action,target_type,target_id,details) VALUES(?,?,?,?,?)');
        $q->execute([$actorId,$action,$targetType,$targetId,$details !== null ? substr($details,0,2000) : null]);
    } catch (Throwable $e) {
        security_log('audit_write_failed', ['action'=>$action,'error_class'=>$e::class]);
    }
}
function admin_count(string $sql,array $params=[]): int {$q=db()->prepare($sql);$q->execute($params);return (int)$q->fetchColumn();}

function current_subscription(int $userId): ?array
{
    $pdo=db();$ownsTransaction=!$pdo->inTransaction();
    try{
        if($ownsTransaction)$pdo->beginTransaction();
        $lock=$pdo->prepare('SELECT id FROM users WHERE id=? FOR UPDATE');$lock->execute([$userId]);
        if(!$lock->fetchColumn()){if($ownsTransaction)$pdo->commit();return null;}
        $pdo->prepare("UPDATE subscriptions SET status='expired' WHERE user_id=? AND status='active' AND ends_at IS NOT NULL AND ends_at<NOW()")->execute([$userId]);
        $q=$pdo->prepare("SELECT s.*,sp.name plan_name,sp.featured_days,sp.lead_limit FROM subscriptions s LEFT JOIN subscription_plans sp ON sp.code=s.plan WHERE s.user_id=? AND s.status='active' AND (s.ends_at IS NULL OR s.ends_at>=NOW()) ORDER BY s.id DESC LIMIT 1");
        $q->execute([$userId]);$active=$q->fetch()?:null;
        if(!$active){
            $next=$pdo->prepare("SELECT id FROM subscriptions WHERE user_id=? AND status='scheduled' AND starts_at<=NOW() ORDER BY starts_at ASC,id ASC LIMIT 1 FOR UPDATE");$next->execute([$userId]);$nextId=(int)($next->fetchColumn()?:0);
            if($nextId>0){
                $pdo->prepare("UPDATE subscriptions SET status='active' WHERE id=?")->execute([$nextId]);
                $benefit=$pdo->prepare("SELECT s.id,s.benefits_applied_at,sp.lead_limit FROM subscriptions s LEFT JOIN subscription_plans sp ON sp.code=s.plan WHERE s.id=? LIMIT 1");$benefit->execute([$nextId]);$b=$benefit->fetch();
                if($b && empty($b['benefits_applied_at'])){
                    $pdo->prepare("UPDATE featured_listings SET status='active' WHERE subscription_id=? AND status='pending' AND starts_at<=NOW()")->execute([$nextId]);
                    if($b['lead_limit']!==null){$pdo->prepare('INSERT INTO lead_wallets(user_id,credits) VALUES(?,?) ON DUPLICATE KEY UPDATE credits=credits+VALUES(credits)')->execute([$userId,(int)$b['lead_limit']]);}
                    $pdo->prepare('UPDATE subscriptions SET benefits_applied_at=NOW() WHERE id=? AND benefits_applied_at IS NULL')->execute([$nextId]);
                }
                $q->execute([$userId]);$active=$q->fetch()?:null;
            }
        }
        if($ownsTransaction)$pdo->commit();return $active;
    }catch(Throwable $e){if($ownsTransaction&&$pdo->inTransaction())$pdo->rollBack();throw $e;}
}

function ensure_free_subscription(int $userId): array
{
    if ($existing = current_subscription($userId)) return $existing;
    $pdo = db(); $ownsTransaction = !$pdo->inTransaction();
    try {
        if ($ownsTransaction) $pdo->beginTransaction();
        $lock = $pdo->prepare('SELECT id FROM users WHERE id=? FOR UPDATE');
        $lock->execute([$userId]);
        if (!$lock->fetchColumn()) throw new RuntimeException('User not found.');
        $existing = current_subscription($userId);
        if (!$existing) {
            $q=$pdo->prepare("INSERT INTO subscriptions(user_id,plan,status,starts_at,price) VALUES(?,'free','active',NOW(),0)");
            $q->execute([$userId]);
            $existing = current_subscription($userId);
        }
        if ($ownsTransaction) $pdo->commit();
        return $existing ?: [];
    } catch (Throwable $e) {
        if ($ownsTransaction && $pdo->inTransaction()) $pdo->rollBack();
        throw $e;
    }
}

function client_ip_hash(): string
{
    // Never trust X-Forwarded-For unless the immediate proxy is explicitly trusted.
    $ip = (string)($_SERVER['REMOTE_ADDR'] ?? 'unknown');
    if (request_from_trusted_proxy()) {
        $xff = trim(explode(',', (string)($_SERVER['HTTP_X_FORWARDED_FOR'] ?? ''))[0]);
        if (filter_var($xff, FILTER_VALIDATE_IP)) $ip = $xff;
    }
    return app_hmac($ip, 'ip');
}

function send_app_email(string $to, string $subject, string $body): bool
{
    $driver = strtolower(env_value('APP_MAIL_DRIVER', 'disabled') ?? 'disabled');
    if ($driver === 'mail') {
        $from = env_value('APP_MAIL_FROM', '') ?? '';
        if (!filter_var($to, FILTER_VALIDATE_EMAIL) || !filter_var($from, FILTER_VALIDATE_EMAIL)) return false;
        $headers = "From: LocalConnect <{$from}>\r\nContent-Type: text/plain; charset=UTF-8";
        return @mail($to, $subject, $body, $headers);
    }
    if ($driver === 'log' && !is_production()) {
        $dir = __DIR__ . '/../storage'; if (!is_dir($dir)) @mkdir($dir, 0700, true);
        $line = "--- " . date(DATE_ATOM) . " ---\nTo: {$to}\nSubject: {$subject}\n{$body}\n\n";
        return file_put_contents($dir . '/mail-development.log', $line, FILE_APPEND | LOCK_EX) !== false;
    }
    return false;
}

function create_auth_token(int $userId, string $purpose, int $ttlSeconds): array
{
    if (!in_array($purpose, ['password_reset','email_verify'], true)) throw new InvalidArgumentException('Invalid token purpose.');
    $selector = bin2hex(random_bytes(8));
    $validator = bin2hex(random_bytes(32));
    $hash = hash('sha256', $validator);
    $expires = (new DateTimeImmutable('+' . $ttlSeconds . ' seconds'))->format('Y-m-d H:i:s');
    $pdo = db();
    $pdo->prepare('DELETE FROM auth_tokens WHERE user_id=? AND purpose=? AND used_at IS NULL')->execute([$userId,$purpose]);
    $q=$pdo->prepare('INSERT INTO auth_tokens(user_id,purpose,selector,token_hash,expires_at,requested_ip_hash) VALUES(?,?,?,?,?,?)');
    $q->execute([$userId,$purpose,$selector,$hash,$expires,client_ip_hash()]);
    return ['selector'=>$selector,'token'=>$validator,'expires_at'=>$expires];
}

function find_valid_auth_token(string $purpose, string $selector, string $validator): ?array
{
    if (!preg_match('/^[a-f0-9]{16}$/', $selector) || !preg_match('/^[a-f0-9]{64}$/', $validator)) return null;
    $q=db()->prepare('SELECT * FROM auth_tokens WHERE purpose=? AND selector=? AND used_at IS NULL AND expires_at>NOW() LIMIT 1');
    $q->execute([$purpose,$selector]); $row=$q->fetch();
    if (!$row || !hash_equals((string)$row['token_hash'], hash('sha256',$validator))) return null;
    return $row;
}

function base32_encode_secret(string $bytes): string
{
    $alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'; $bits=''; $out='';
    foreach (str_split($bytes) as $c) $bits .= str_pad(decbin(ord($c)),8,'0',STR_PAD_LEFT);
    foreach (str_split($bits,5) as $chunk) { if(strlen($chunk)<5)$chunk=str_pad($chunk,5,'0');$out.=$alphabet[bindec($chunk)]; }
    return $out;
}
function base32_decode_secret(string $value): string
{
    $alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'; $value=strtoupper(preg_replace('/[^A-Z2-7]/i','',$value)??'');$bits='';
    foreach(str_split($value) as $c){$p=strpos($alphabet,$c);if($p===false)continue;$bits.=str_pad(decbin($p),5,'0',STR_PAD_LEFT);} $out='';
    foreach(str_split($bits,8) as $chunk){if(strlen($chunk)===8)$out.=chr(bindec($chunk));} return $out;
}
function totp_code(string $base32Secret, ?int $time=null): string
{
    $time ??= time(); $counter=intdiv($time,30); $bin='';
    for($i=7;$i>=0;$i--)$bin.=chr(($counter>>(8*$i))&0xff);
    $hash=hash_hmac('sha1',$bin,base32_decode_secret($base32Secret),true);$offset=ord($hash[19])&0x0f;
    $num=((ord($hash[$offset])&0x7f)<<24)|((ord($hash[$offset+1])&0xff)<<16)|((ord($hash[$offset+2])&0xff)<<8)|(ord($hash[$offset+3])&0xff);
    return str_pad((string)($num%1000000),6,'0',STR_PAD_LEFT);
}
function verify_totp(string $secret, string $code, ?int $lastUsedStep=null): ?int
{
    if(!preg_match('/^\d{6}$/',$code))return null;$step=intdiv(time(),30);
    foreach([-1,0,1] as $delta){$candidate=$step+$delta;if($lastUsedStep!==null&&$candidate<=$lastUsedStep)continue;if(hash_equals(totp_code($secret,$candidate*30),$code))return $candidate;}
    return null;
}
function encrypt_sensitive(string $plaintext): array
{
    $key=app_key_bytes(true);
    if(function_exists('sodium_crypto_secretbox')){$nonce=random_bytes(SODIUM_CRYPTO_SECRETBOX_NONCEBYTES);$cipher=sodium_crypto_secretbox($plaintext,$nonce,$key);return ['ciphertext'=>base64_encode($cipher),'nonce'=>base64_encode($nonce),'alg'=>'sodium_secretbox'];}
    $nonce=random_bytes(12);$tag='';$cipher=openssl_encrypt($plaintext,'aes-256-gcm',$key,OPENSSL_RAW_DATA,$nonce,$tag);
    if($cipher===false)throw new RuntimeException('Secret encryption unavailable.');return ['ciphertext'=>base64_encode($cipher.$tag),'nonce'=>base64_encode($nonce),'alg'=>'aes-256-gcm'];
}
function decrypt_sensitive(string $ciphertext,string $nonce,string $alg): string
{
    $key=app_key_bytes(true);$cipher=base64_decode($ciphertext,true);$iv=base64_decode($nonce,true);if($cipher===false||$iv===false)throw new RuntimeException('Encrypted secret is invalid.');
    if($alg==='sodium_secretbox'&&function_exists('sodium_crypto_secretbox_open')){$plain=sodium_crypto_secretbox_open($cipher,$iv,$key);if($plain===false)throw new RuntimeException('Secret decryption failed.');return $plain;}
    if($alg==='aes-256-gcm'&&strlen($cipher)>=16){$tag=substr($cipher,-16);$body=substr($cipher,0,-16);$plain=openssl_decrypt($body,'aes-256-gcm',$key,OPENSSL_RAW_DATA,$iv,$tag);if($plain===false)throw new RuntimeException('Secret decryption failed.');return $plain;}
    throw new RuntimeException('Secret encryption algorithm is unavailable.');
}

/**
 * Phase 3 payment-method helpers.
 * Gateway secrets are intentionally never accepted from browser forms or stored
 * in the application database. They are read only from the process environment.
 */
function supported_payment_gateways(): array
{
    return [
        'razorpay' => [
            'label' => 'Razorpay',
            'required_env' => [
                'PAYMENT_RAZORPAY_KEY_ID',
                'PAYMENT_RAZORPAY_KEY_SECRET',
                'PAYMENT_RAZORPAY_WEBHOOK_SECRET',
            ],
        ],
    ];
}

function valid_upi_id(string $value): bool
{
    $value = trim($value);
    if ($value === '' || text_length($value) > 190) return false;
    return (bool)preg_match('/^[A-Za-z0-9._-]{2,128}@[A-Za-z0-9._-]{2,64}$/', $value);
}

function normalize_currency(mixed $value): string
{
    $currency = strtoupper(clean_text($value, 3, true, 'Currency'));
    if (!preg_match('/^[A-Z]{3}$/', $currency)) throw new RuntimeException('Currency must be a 3-letter ISO code.');
    // Current subscription plan prices are INR-only. Expanding currencies requires
    // a plan-price model and FX/tax review in a later migration.
    if ($currency !== 'INR') throw new RuntimeException('Only INR is supported by the current subscription catalogue.');
    return $currency;
}

function payment_gateway_configuration_status(string $gatewayCode): array
{
    $gateways = supported_payment_gateways();
    if (!isset($gateways[$gatewayCode])) {
        return ['configured'=>false,'label'=>'Unsupported gateway','missing'=>[],'indicators'=>[]];
    }
    $required = $gateways[$gatewayCode]['required_env'];
    $missing = [];
    $indicators = [];
    foreach ($required as $name) {
        $present = trim((string)(env_value($name, '') ?? '')) !== '' && !str_contains((string)env_value($name, ''), 'REPLACE_WITH_');
        if (!$present) $missing[] = $name;
        $indicators[$name] = $present ? 'configured' : 'missing';
    }
    if ($gatewayCode === 'razorpay') {
        $keyId = trim((string)(env_value('PAYMENT_RAZORPAY_KEY_ID', '') ?? ''));
        if (str_starts_with($keyId, 'rzp_live_') && !env_bool('PAYMENT_ALLOW_LIVE', false)) {
            $missing[] = 'PAYMENT_ALLOW_LIVE';
            $indicators['PAYMENT_ALLOW_LIVE'] = 'disabled';
        }
    }
    return [
        'configured' => count($missing) === 0,
        'label' => (string)$gateways[$gatewayCode]['label'],
        'missing' => $missing,
        'indicators' => $indicators,
    ];
}

function payment_method_configuration_status(array $method): array
{
    $type = (string)($method['method_type'] ?? '');
    if ($type === 'gateway') {
        $status = payment_gateway_configuration_status((string)($method['gateway_code'] ?? ''));
        return ['configured'=>$status['configured'],'summary'=>$status['configured'] ? 'Gateway environment configured' : 'Gateway environment incomplete','detail'=>$status];
    }
    if ($type === 'upi') {
        $ok = valid_upi_id((string)($method['merchant_upi_id'] ?? '')) && trim((string)($method['display_instructions'] ?? '')) !== '';
        return ['configured'=>$ok,'summary'=>$ok ? 'Manual UPI instructions configured' : 'UPI ID/instructions incomplete','detail'=>[]];
    }
    if ($type === 'bank_transfer') {
        $ok = trim((string)($method['bank_beneficiary'] ?? '')) !== '' && trim((string)($method['display_instructions'] ?? '')) !== '';
        return ['configured'=>$ok,'summary'=>$ok ? 'Bank transfer instructions configured' : 'Beneficiary/instructions incomplete','detail'=>[]];
    }
    return ['configured'=>false,'summary'=>'Unsupported payment method type','detail'=>[]];
}

function payment_method_audit_snapshot(array $method): array
{
    $keys = ['id','code','name','method_type','gateway_code','audience','currency','merchant_upi_id','bank_beneficiary','bank_reference','display_instructions','display_order','is_active'];
    $out = [];
    foreach ($keys as $key) {
        if (array_key_exists($key, $method)) $out[$key] = $method[$key];
    }
    return $out;
}

function record_payment_method_audit(int $methodId, int $adminId, string $action, ?array $before, ?array $after): void
{
    $allowed = ['create','update','activate','deactivate','reorder'];
    if (!in_array($action, $allowed, true)) $action = 'update';
    $q = db()->prepare('INSERT INTO payment_method_audit(payment_method_id,admin_user_id,action,before_json,after_json) VALUES(?,?,?,?,?)');
    $q->execute([
        $methodId,
        $adminId,
        $action,
        $before ? json_encode(payment_method_audit_snapshot($before), JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) : null,
        $after ? json_encode(payment_method_audit_snapshot($after), JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) : null,
    ]);
}

function active_payment_methods_for_role(string $role, string $currency = 'INR'): array
{
    if (!in_array($role, ['provider','business'], true)) return [];
    $currency = strtoupper($currency);
    if (!preg_match('/^[A-Z]{3}$/', $currency)) return [];
    $q = db()->prepare("SELECT * FROM payment_methods WHERE is_active=1 AND currency=? AND audience IN (?, 'both') ORDER BY display_order ASC,id ASC");
    $q->execute([$currency,$role]);
    return $q->fetchAll();
}
