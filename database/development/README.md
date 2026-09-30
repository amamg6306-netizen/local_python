# Development database note

The production-hardening artifact intentionally contains no built-in demo users or known passwords. For local testing, create disposable accounts through the normal registration flow and create a disposable admin with `tools/create_admin.php` using environment-supplied credentials.

Never use production customer data in a local development database.
