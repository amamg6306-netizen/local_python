# Production Phase 6 — hardening, QA and deployment rehearsal

This cumulative build adds production HTTPS/runtime policy, nonce CSP/security headers, stricter web/upload path protection, password-recovery/verification rate limits, password-hash rehashing, webhook body bounding, log redaction, deployment examples, least-privilege DB guidance, backup/restore tooling, secret/dependency scans, ASVS mapping, a versioned Phase 6 support-index migration and an explicit evidence-based live release gate.

The build is intentionally **NOT READY FOR LIVE PAYMENTS** because this packaging environment does not have the merchant sandbox credentials, reachable webhook endpoint, production MySQL/PHP stack, legal/financial approval, independent penetration test or production smoke-test evidence required by `tools/release_gate.php`.
