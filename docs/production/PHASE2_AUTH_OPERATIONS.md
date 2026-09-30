# Phase 2 authentication operations

- Production should set `APP_REQUIRE_EMAIL_VERIFICATION=true` and configure a real mail-delivery mechanism before opening registration.
- `APP_ADMIN_MFA_REQUIRED=true` makes admin pages redirect to MFA setup/challenge until the session is verified.
- TOTP secrets are encrypted with `APP_KEY`; rotating `APP_KEY` requires an explicit secret re-encryption procedure. Do not rotate it blindly.
- Password reset increments `users.session_version`, invalidating existing authenticated sessions on their next request.
- Blocking/unblocking through admin user management also increments session version so a blocked user's old session cannot continue.
- Login throttling defaults to 5 failures in 15 minutes and a 15-minute block; tune with production telemetry to avoid both brute-force exposure and user denial-of-service.
- Development-only `APP_MAIL_DRIVER=log` writes reset/verification links to `storage/mail-development.log`. Never use this driver in production.
