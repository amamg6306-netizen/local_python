# Security and architecture decisions

- **Server authority:** roles, ownership, plan audience, amount, tax, entitlement and payment status are decided server-side. Client values are not authoritative.
- **Payment data scope:** LocalConnect never provides fields for raw card number or CVV. Hosted PSP checkout is used. PCI scope still requires merchant/acquirer review; this code does not claim PCI certification.
- **Webhook trust:** HMAC signature validation is mandatory, exact raw request body is used, payload size is bounded before processing, event keys are unique/idempotent, and successful browser return alone never grants entitlement.
- **Secrets:** production DB/payment secrets are environment/secret-manager values; admin UI exposes only status indicators. Source/config examples contain placeholders only.
- **Sessions:** strict cookie-only sessions, HttpOnly/Secure/SameSite, idle/absolute expiry and periodic/login rotation are enforced. Production HTTP is redirected to HTTPS using explicitly trusted proxy information only.
- **Browser policy:** nonce-based CSP, HSTS, frame denial, MIME sniffing protection, restrictive permissions policy and referrer policy are emitted. Inline event-handler attributes were removed so CSP can set `script-src-attr 'none'`.
- **Uploads:** file size, MIME, decoded dimensions/pixel count and managed destination are checked; production requires GD decode/re-encode and the upload directory disables executable handlers.
- **Authorization:** customer/provider/business/admin routes retain server-side role/ownership checks. Sensitive admin payment operations require MFA and re-authentication.
- **Authentication abuse:** login plus password-reset/verification-delivery endpoints are rate limited; recovery responses avoid account enumeration.
- **Logging:** logs intentionally exclude password/secret/token/cookie keys and redact common credential patterns. Payment and admin state changes also have database audit/status history.
- **Database:** PDO native prepared statements are required. Web runtime uses a least-privilege account; migrations use a separate operator account. Versioned production migrations are non-destructive where feasible and have preflight/rollback companions.
- **Performance:** high-growth lists are bounded/paginated, upload decoding is memory bounded, telemetry is opt-in/redacted, and payment reconciliation retries have batch/queue/attempt ceilings.
- **Residual risk:** CDN/PSP third-party JavaScript, hosting/TLS configuration, email transport, merchant account configuration and infrastructure security remain external trust boundaries requiring staging/production verification.
