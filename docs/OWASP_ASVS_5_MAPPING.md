# OWASP ASVS 5.0.0 applicability map

This is an engineering coverage map, **not an OWASP certification or claim of full ASVS conformance**. OWASP currently identifies ASVS 5.0.0 as the latest stable version. Exact requirement IDs should be rechecked against the official ASVS 5.0.0 CSV/JSON during an independent assessment.

| ASVS 5 area | LocalConnect control/evidence | Status / remaining verification |
|---|---|---|
| V1 Encoding & Sanitization | `e()` contextual HTML escaping, JSON hex escaping for checkout bootstrap data; no `eval()` | Implemented; browser XSS regression still required |
| V2 Validation & Business Logic | strict server-side plan/role/price verification, request validation, immutable payment snapshots | Implemented; DB/browser tampering tests required |
| V3 Web Frontend Security | nonce CSP, `script-src-attr 'none'`, HSTS, frame denial, Referrer/Permissions policies | Implemented; real-browser CSP/PSP compatibility required |
| V4 API & Web Service | webhook POST-only, bounded body, signed raw-body HMAC, idempotent event key, server reconciliation | Implemented; sandbox webhook acceptance required |
| V5 File Handling | bounded size, MIME, dimensions/pixels, production GD re-encode, non-executable upload directory | Implements controls aligned with V5.2 upload-size/content/pixel protections; host-level abuse tests required |
| V6 Authentication | password hashing/rehash, anti-enumeration recovery, throttling, admin TOTP MFA | Implemented; mail and account lifecycle tests required |
| V6.5 MFA | TOTP seed from CSPRNG/encrypted storage; TOTP replay step tracked and 30-second steps used | Aligned with relevant V6.5 controls; independent verification required |
| V7 Session Management | strict cookie-only session, Secure/HttpOnly/SameSite, rotation, idle/absolute expiry | Implemented; browser/session abuse tests required |
| V8 Authorization | role and ownership checks, admin MFA/re-auth for sensitive payment decisions | Implemented; IDOR matrix remains a release gate |
| V11 Cryptography | `random_bytes`, HMAC, password hashing, sodium secretbox or AES-GCM for MFA seed | Implemented with platform crypto dependency; key rotation is operationally sensitive |
| V12 Secure Communication | production HTTPS requirement, HSTS, trusted-proxy allowlist | Implemented in app/example config; TLS scan required |
| V13 Configuration | environment secrets, dedicated DB account template, protected internal directories | Aligned with least-privilege backend configuration; host verification required |
| V14 Data Protection | secrets excluded from UI/DB where applicable, card/CVV excluded, log redaction | Implemented in app; privacy/data-retention review required |
| V15 Secure Coding & Architecture | versioned migrations, fail-safe payment state machine, bounded worker retries | Implemented; independent code review required |
| V16 Security Logging & Error Handling | auth/admin/payment audit records, redacted security logs, production error display off | Aligned with V16.2 sensitive-log handling and V16.3 security-event logging; SIEM/retention/time-sync are deployment responsibilities |

The project targets the control depth appropriate to an internet-facing marketplace handling account and payment metadata, but release documentation intentionally does not declare a formal ASVS level achieved. A qualified independent reviewer should select the applicable ASVS level and produce the final evidence-based assessment.
