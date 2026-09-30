# PHP → Python / Flask Map

> Phase 1 migration map. This is a design/traceability artifact, not an implementation claim. Legacy browser URLs will be preserved by Flask even when the underlying Python module name changes.

PHP files mapped: **93**.

## File-level mapping

| Existing PHP file | Proposed Python/Jinja replacement | Notes |
|---|---|---|
| `403.php` | `app.py error handlers + templates/errors/*.html` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `404.php` | `app.py error handlers + templates/errors/*.html` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `about.php` | `routes/main.py + matching Jinja template` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `admin/_nav.php` | `templates/admin/_nav.html` | Template partial only. |
| `admin/advertisements.php` | `routes/admin.py + templates/admin/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `admin/businesses.php` | `routes/admin.py + templates/admin/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `admin/categories.php` | `routes/admin.py + templates/admin/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `admin/index.php` | `routes/admin.py + templates/admin/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `admin/mfa.php` | `routes/admin.py + templates/admin/*` | Expose compatibility route at the same existing URL unless documented otherwise. Phase 4 implemented; runtime parity suite prepared. |
| `admin/payment-detail.php` | `routes/admin.py + templates/admin/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `admin/payment-method-edit.php` | `routes/admin.py + templates/admin/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `admin/payment-methods.php` | `routes/admin.py + templates/admin/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `admin/payments.php` | `routes/admin.py + templates/admin/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `admin/providers.php` | `routes/admin.py + templates/admin/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `admin/reauth.php` | `routes/admin.py + templates/admin/*` | Expose compatibility route at the same existing URL unless documented otherwise. Phase 4 implemented; runtime parity suite prepared. |
| `admin/reports.php` | `routes/admin.py + templates/admin/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `admin/requests.php` | `routes/admin.py + templates/admin/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `admin/reviews.php` | `routes/admin.py + templates/admin/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `admin/services.php` | `routes/admin.py + templates/admin/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `admin/subscriptions.php` | `routes/admin.py + templates/admin/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `admin/users.php` | `routes/admin.py + templates/admin/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `ajax/favorite.php` | `routes/api.py` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `auth/forgot-password.php` | `routes/auth.py + templates/auth/*` | Expose compatibility route at the same existing URL unless documented otherwise. Phase 4 implemented; runtime parity suite prepared. |
| `auth/login.php` | `routes/auth.py + templates/auth/*` | Expose compatibility route at the same existing URL unless documented otherwise. Phase 4 implemented; runtime parity suite prepared. |
| `auth/logout.php` | `routes/auth.py + templates/auth/*` | Expose compatibility route at the same existing URL unless documented otherwise. Phase 4 implemented; runtime parity suite prepared. |
| `auth/register.php` | `routes/auth.py + templates/auth/*` | Expose compatibility route at the same existing URL unless documented otherwise. Phase 4 implemented; runtime parity suite prepared. |
| `auth/resend-verification.php` | `routes/auth.py + templates/auth/*` | Expose compatibility route at the same existing URL unless documented otherwise. Phase 4 implemented; runtime parity suite prepared. |
| `auth/reset-password.php` | `routes/auth.py + templates/auth/*` | Expose compatibility route at the same existing URL unless documented otherwise. Phase 4 implemented; runtime parity suite prepared. |
| `auth/verify-email.php` | `routes/auth.py + templates/auth/*` | Expose compatibility route at the same existing URL unless documented otherwise. Phase 4 implemented; runtime parity suite prepared. |
| `billing/cancel.php` | `routes/billing.py + services/billing_service.py + templates/billing/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `billing/gateway-return.php` | `routes/billing.py + services/billing_service.py + templates/billing/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `billing/gateway.php` | `routes/billing.py + services/billing_service.py + templates/billing/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `billing/history.php` | `routes/billing.py + services/billing_service.py + templates/billing/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `billing/manual.php` | `routes/billing.py + services/billing_service.py + templates/billing/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `billing/payment-method.php` | `routes/billing.py + services/billing_service.py + templates/billing/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `billing/select-method.php` | `routes/billing.py + services/billing_service.py + templates/billing/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `billing/start.php` | `routes/billing.py + services/billing_service.py + templates/billing/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `business.php` | `routes/main.py + matching Jinja template` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `business/dashboard.php` | `routes/business.py + templates/business/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `business/profile.php` | `routes/business.py + templates/business/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `business/requests.php` | `routes/business.py + templates/business/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `business/services.php` | `routes/business.py + templates/business/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `business/subscription.php` | `routes/business.py + templates/business/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `categories.php` | `routes/main.py + matching Jinja template` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `config/app.php` | `config/settings.py + utils/security.py` | Shared runtime/helper module; not a public Flask route. |
| `config/database.php` | `extensions.py + config/settings.py` | Shared runtime/helper module; not a public Flask route. |
| `contact.php` | `routes/main.py + matching Jinja template` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `customer/dashboard.php` | `routes/customer.py + templates/customer/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `customer/requests.php` | `routes/customer.py + templates/customer/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `favorites.php` | `routes/customer.py + domain template` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `includes/auth.php` | `services/auth_service.py + utils/decorators.py` | Shared runtime/helper module; not a public Flask route. |
| `includes/billing.php` | `services/billing_service.py` | Shared runtime/helper module; not a public Flask route. |
| `includes/footer.php` | `templates/_footer.html / templates/base.html` | Shared runtime/helper module; not a public Flask route. |
| `includes/functions.php` | `services/auth_service.py + services/marketplace_service.py + services/billing_service.py + utils/{auth,security,logging}.py` | Shared runtime/helper module; not a public Flask route. |
| `includes/header.php` | `templates/_header.html / templates/base.html` | Shared runtime/helper module; not a public Flask route. |
| `includes/navbar.php` | `templates/_navbar.html` | Shared runtime/helper module; not a public Flask route. |
| `includes/performance.php` | `utils/performance.py` | Shared runtime/helper module; not a public Flask route. |
| `includes/security.php` | `utils/security.py` | Shared runtime/helper module; not a public Flask route. |
| `index.php` | `routes/main.py + matching Jinja template` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `login.php` | `routes/auth.py + templates/auth/*` | Expose compatibility route at the same existing URL unless documented otherwise. Phase 4 implemented; runtime parity suite prepared. |
| `logout.php` | `routes/auth.py + templates/auth/*` | Expose compatibility route at the same existing URL unless documented otherwise. Phase 4 implemented; runtime parity suite prepared. |
| `notifications.php` | `routes/main.py + matching Jinja template` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `post-requirement.php` | `routes/customer.py + domain template` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `privacy.php` | `routes/main.py + matching Jinja template` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `provider.php` | `routes/main.py + matching Jinja template` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `provider/available-requirements.php` | `routes/provider.py + templates/provider/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `provider/dashboard.php` | `routes/provider.py + templates/provider/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `provider/portfolio.php` | `routes/provider.py + templates/provider/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `provider/profile.php` | `routes/provider.py + templates/provider/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `provider/requests.php` | `routes/provider.py + templates/provider/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `provider/services.php` | `routes/provider.py + templates/provider/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `provider/subscription.php` | `routes/provider.py + templates/provider/*` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `register.php` | `routes/auth.py + templates/auth/*` | Expose compatibility route at the same existing URL unless documented otherwise. Phase 4 implemented; runtime parity suite prepared. |
| `report.php` | `routes/main.py + matching Jinja template` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `request-details.php` | `routes/main.py + matching Jinja template` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `request-service.php` | `routes/customer.py + domain template` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `reviews.php` | `routes/main.py + matching Jinja template` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `search.php` | `routes/main.py + matching Jinja template` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `terms.php` | `routes/main.py + matching Jinja template` | Expose compatibility route at the same existing URL unless documented otherwise. |
| `tests/phase1/php_helper_smoke.php` | `tests/test_helpers.py` | Port assertions/fixtures; remove PHP execution dependency. |
| `tests/phase2/php_security_helpers.php` | `tests/test_security_helpers.py` | Port assertions/fixtures; remove PHP execution dependency. |
| `tests/phase3/php_payment_helpers.php` | `tests/test_payment_method_helpers.py` | Port assertions/fixtures; remove PHP execution dependency. |
| `tests/phase4/php_billing_helpers.php` | `tests/test_billing_helpers.py` | Port assertions/fixtures; remove PHP execution dependency. |
| `tests/phase5/memory_fixture.php` | `tests/performance/memory_fixture.py` | Port assertions/fixtures; remove PHP execution dependency. |
| `tests/phase6/php_security_helpers.php` | `tests/test_hardening_helpers.py` | Port assertions/fixtures; remove PHP execution dependency. |
| `tools/check_production_config.php` | `scripts/check_production_config.py` | CLI/operations only; must never run on every web request/startup. |
| `tools/create_admin.php` | `scripts/create_admin.py` | CLI/operations only; must never run on every web request/startup. |
| `tools/payment_reconciliation_worker.php` | `scripts/payment_reconciliation_worker.py` | CLI/operations only; must never run on every web request/startup. |
| `tools/performance_gate.php` | `scripts/performance_gate.py` | CLI/operations only; must never run on every web request/startup. |
| `tools/performance_log_report.php` | `scripts/performance_log_report.py` | CLI/operations only; must never run on every web request/startup. |
| `tools/performance_seed.php` | `scripts/performance_seed.py` | CLI/operations only; must never run on every web request/startup. |
| `tools/release_gate.php` | `scripts/release_gate.py` | CLI/operations only; must never run on every web request/startup. |
| `webhooks/razorpay.php` | `routes/webhooks.py + services/billing_service.py` | Expose compatibility route at the same existing URL unless documented otherwise. |

## Shared function-level mapping

| PHP function | Existing file | Python destination / responsibility |
|---|---|---|
| `env_value()` | `config/app.php` | `config/settings.py / utils/security.py` |
| `env_bool()` | `config/app.php` | `config/settings.py / utils/security.py` |
| `env_int()` | `config/app.php` | `config/settings.py / utils/security.py` |
| `app_env()` | `config/app.php` | `config/settings.py / utils/security.py` |
| `is_production()` | `config/app.php` | `config/settings.py / utils/security.py` |
| `app_debug()` | `config/app.php` | `config/settings.py / utils/security.py` |
| `request_from_trusted_proxy()` | `config/app.php` | `config/settings.py / utils/security.py` |
| `request_is_https()` | `config/app.php` | `config/settings.py / utils/security.py` |
| `configured_base_path()` | `config/app.php` | `config/settings.py / utils/security.py` |
| `app_origin()` | `config/app.php` | `config/settings.py / utils/security.py` |
| `app_key_bytes()` | `config/app.php` | `config/settings.py / utils/security.py` |
| `app_hmac()` | `config/app.php` | `config/settings.py / utils/security.py` |
| `configure_runtime_error_policy()` | `config/app.php` | `config/settings.py / utils/security.py` |
| `enforce_production_https()` | `config/app.php` | `config/settings.py / utils/security.py` |
| `production_config_errors()` | `config/app.php` | `config/settings.py / utils/security.py` |
| `db_config()` | `config/database.php` | `extensions.py` |
| `db()` | `config/database.php` | `extensions.py` |
| `clear_auth_session()` | `includes/auth.php` | `services/auth_service.py / utils/decorators.py` |
| `enforce_session_lifecycle()` | `includes/auth.php` | `services/auth_service.py / utils/decorators.py` |
| `current_user()` | `includes/auth.php` | `services/auth_service.py / utils/decorators.py` |
| `is_logged_in()` | `includes/auth.php` | `services/auth_service.py / utils/decorators.py` |
| `require_guest()` | `includes/auth.php` | `services/auth_service.py / utils/decorators.py` |
| `require_login()` | `includes/auth.php` | `services/auth_service.py / utils/decorators.py` |
| `admin_mfa_record()` | `includes/auth.php` | `services/auth_service.py / utils/decorators.py` |
| `admin_mfa_needed()` | `includes/auth.php` | `services/auth_service.py / utils/decorators.py` |
| `admin_mfa_verified()` | `includes/auth.php` | `services/auth_service.py / utils/decorators.py` |
| `require_role()` | `includes/auth.php` | `services/auth_service.py / utils/decorators.py` |
| `require_recent_admin_reauth()` | `includes/auth.php` | `services/auth_service.py / utils/decorators.py` |
| `require_admin_mfa_for_sensitive()` | `includes/auth.php` | `services/auth_service.py / utils/decorators.py` |
| `login_rate_keys()` | `includes/auth.php` | `services/auth_service.py / utils/decorators.py` |
| `login_rate_check()` | `includes/auth.php` | `services/auth_service.py / utils/decorators.py` |
| `login_rate_failure()` | `includes/auth.php` | `services/auth_service.py / utils/decorators.py` |
| `login_rate_success()` | `includes/auth.php` | `services/auth_service.py / utils/decorators.py` |
| `auth_action_rate_keys()` | `includes/auth.php` | `services/auth_service.py / utils/decorators.py` |
| `auth_action_rate_check()` | `includes/auth.php` | `services/auth_service.py / utils/decorators.py` |
| `auth_action_rate_hit()` | `includes/auth.php` | `services/auth_service.py / utils/decorators.py` |
| `csp_nonce()` | `includes/security.php` | `utils/security.py` |
| `hsts_header_value()` | `includes/security.php` | `utils/security.py` |
| `localconnect_csp()` | `includes/security.php` | `utils/security.py` |
| `apply_browser_security_headers()` | `includes/security.php` | `utils/security.py` |
| `apply_api_security_headers()` | `includes/security.php` | `utils/security.py` |
| `enforce_request_body_limit()` | `includes/security.php` | `utils/security.py` |
| `performance_metrics_enabled()` | `includes/performance.php` | `utils/performance.py` |
| `performance_metrics_path()` | `includes/performance.php` | `utils/performance.py` |
| `rotate_performance_log_if_needed()` | `includes/performance.php` | `utils/performance.py` |
| `performance_register_request_metrics()` | `includes/performance.php` | `utils/performance.py` |
| `money_minor()` | `includes/billing.php` | `services/billing_service.py` |
| `money_decimal_from_minor()` | `includes/billing.php` | `services/billing_service.py` |
| `billing_plan_for_role()` | `includes/billing.php` | `services/billing_service.py` |
| `plan_price_breakdown()` | `includes/billing.php` | `services/billing_service.py` |
| `checkout_token_hash()` | `includes/billing.php` | `services/billing_service.py` |
| `create_checkout_intent()` | `includes/billing.php` | `services/billing_service.py` |
| `expire_checkout_intents()` | `includes/billing.php` | `services/billing_service.py` |
| `checkout_intent()` | `includes/billing.php` | `services/billing_service.py` |
| `configured_payment_methods_for_role()` | `includes/billing.php` | `services/billing_service.py` |
| `payment_history_add()` | `includes/billing.php` | `services/billing_service.py` |
| `payment_by_id()` | `includes/billing.php` | `services/billing_service.py` |
| `create_payment_for_intent()` | `includes/billing.php` | `services/billing_service.py` |
| `razorpay_credentials()` | `includes/billing.php` | `services/billing_service.py` |
| `razorpay_api_request()` | `includes/billing.php` | `services/billing_service.py` |
| `create_razorpay_order()` | `includes/billing.php` | `services/billing_service.py` |
| `verify_razorpay_callback_signature()` | `includes/billing.php` | `services/billing_service.py` |
| `record_verified_gateway_callback()` | `includes/billing.php` | `services/billing_service.py` |
| `remote_razorpay_payment()` | `includes/billing.php` | `services/billing_service.py` |
| `remote_razorpay_order()` | `includes/billing.php` | `services/billing_service.py` |
| `verify_remote_payment_matches()` | `includes/billing.php` | `services/billing_service.py` |
| `subscription_end_from()` | `includes/billing.php` | `services/billing_service.py` |
| `activate_entitlement_for_payment()` | `includes/billing.php` | `services/billing_service.py` |
| `mark_payment_paid_after_reconciliation()` | `includes/billing.php` | `services/billing_service.py` |
| `reconcile_razorpay_payment()` | `includes/billing.php` | `services/billing_service.py` |
| `mark_payment_failed()` | `includes/billing.php` | `services/billing_service.py` |
| `revoke_entitlement_for_payment()` | `includes/billing.php` | `services/billing_service.py` |
| `mark_refund_state()` | `includes/billing.php` | `services/billing_service.py` |
| `mark_disputed()` | `includes/billing.php` | `services/billing_service.py` |
| `razorpay_webhook_signature_valid()` | `includes/billing.php` | `services/billing_service.py` |
| `webhook_client_allowed()` | `includes/billing.php` | `services/billing_service.py` |
| `webhook_event_identifiers()` | `includes/billing.php` | `services/billing_service.py` |
| `find_local_payment_by_provider_refs()` | `includes/billing.php` | `services/billing_service.py` |
| `enqueue_payment_reconciliation_job()` | `includes/billing.php` | `services/billing_service.py` |
| `run_payment_reconciliation_batch()` | `includes/billing.php` | `services/billing_service.py` |
| `process_razorpay_webhook()` | `includes/billing.php` | `services/billing_service.py` |
| `submit_manual_payment_reference()` | `includes/billing.php` | `services/billing_service.py` |
| `verify_manual_payment_admin()` | `includes/billing.php` | `services/billing_service.py` |
| `cancel_checkout_payment()` | `includes/billing.php` | `services/billing_service.py` |
| `base_url()` | `includes/functions.php` | `services/auth_service.py / services/marketplace_service.py / Flask/Jinja helpers` |
| `absolute_url()` | `includes/functions.php` | `services/auth_service.py / services/marketplace_service.py / Flask/Jinja helpers` |
| `e()` | `includes/functions.php` | `services/auth_service.py / services/marketplace_service.py / Flask/Jinja helpers` |
| `redirect()` | `includes/functions.php` | `services/auth_service.py / services/marketplace_service.py / Flask/Jinja helpers` |
| `safe_admin_return()` | `includes/functions.php` | `services/auth_service.py / services/marketplace_service.py / Flask/Jinja helpers` |
| `csrf_token()` | `includes/functions.php` | `services/auth_service.py / services/marketplace_service.py / Flask/Jinja helpers` |
| `csrf_field()` | `includes/functions.php` | `services/auth_service.py / services/marketplace_service.py / Flask/Jinja helpers` |
| `verify_csrf()` | `includes/functions.php` | `services/auth_service.py / services/marketplace_service.py / Flask/Jinja helpers` |
| `flash()` | `includes/functions.php` | `services/auth_service.py / services/marketplace_service.py / Flask/Jinja helpers` |
| `text_length()` | `includes/functions.php` | `services/auth_service.py / services/marketplace_service.py / Flask/Jinja helpers` |
| `clean_text()` | `includes/functions.php` | `services/marketplace_service.py / services/auth_service.py` |
| `nullable_money()` | `includes/functions.php` | `services/marketplace_service.py / services/auth_service.py` |
| `valid_phone_or_empty()` | `includes/functions.php` | `services/marketplace_service.py / services/auth_service.py` |
| `valid_pincode_or_empty()` | `includes/functions.php` | `services/marketplace_service.py / services/auth_service.py` |
| `validated_http_url()` | `includes/functions.php` | `services/marketplace_service.py / services/auth_service.py` |
| `nullable_date()` | `includes/functions.php` | `services/marketplace_service.py / services/auth_service.py` |
| `nullable_time()` | `includes/functions.php` | `services/marketplace_service.py / services/auth_service.py` |
| `nullable_datetime_local()` | `includes/functions.php` | `services/marketplace_service.py / services/auth_service.py` |
| `safe_local_path()` | `includes/functions.php` | `services/upload_service.py` |
| `pagination_window()` | `includes/functions.php` | `services/auth_service.py / services/marketplace_service.py / Flask/Jinja helpers` |
| `trim_page_results()` | `includes/functions.php` | `services/auth_service.py / services/marketplace_service.py / Flask/Jinja helpers` |
| `pagination_href()` | `includes/functions.php` | `services/auth_service.py / services/marketplace_service.py / Flask/Jinja helpers` |
| `pagination_nav()` | `includes/functions.php` | `services/auth_service.py / services/marketplace_service.py / Flask/Jinja helpers` |
| `release_session_lock()` | `includes/functions.php` | `services/auth_service.py / services/marketplace_service.py / Flask/Jinja helpers` |
| `role_label()` | `includes/functions.php` | `services/auth_service.py / services/marketplace_service.py / Flask/Jinja helpers` |
| `dashboard_for()` | `includes/functions.php` | `services/auth_service.py / services/marketplace_service.py / Flask/Jinja helpers` |
| `slugify()` | `includes/functions.php` | `services/auth_service.py / services/marketplace_service.py / Flask/Jinja helpers` |
| `ini_size_bytes()` | `includes/functions.php` | `services/upload_service.py` |
| `image_decode_fits_memory()` | `includes/functions.php` | `services/upload_service.py` |
| `upload_image()` | `includes/functions.php` | `services/upload_service.py` |
| `delete_managed_upload()` | `includes/functions.php` | `services/upload_service.py` |
| `rating_summary()` | `includes/functions.php` | `domain service/repository layer` |
| `is_favorite()` | `includes/functions.php` | `domain service/repository layer` |
| `unread_notification_count()` | `includes/functions.php` | `domain service/repository layer` |
| `redact_log_scalar()` | `includes/functions.php` | `services/auth_service.py / services/marketplace_service.py / Flask/Jinja helpers` |
| `security_log()` | `includes/functions.php` | `services/auth_service.py / services/marketplace_service.py / Flask/Jinja helpers` |
| `log_activity()` | `includes/functions.php` | `domain service/repository layer` |
| `admin_count()` | `includes/functions.php` | `domain service/repository layer` |
| `current_subscription()` | `includes/functions.php` | `domain service/repository layer` |
| `ensure_free_subscription()` | `includes/functions.php` | `domain service/repository layer` |
| `client_ip_hash()` | `includes/functions.php` | `services/auth_service.py / services/marketplace_service.py / Flask/Jinja helpers` |
| `send_app_email()` | `includes/functions.php` | `services/auth_service.py / utils/security.py` |
| `create_auth_token()` | `includes/functions.php` | `services/auth_service.py / utils/security.py` |
| `find_valid_auth_token()` | `includes/functions.php` | `services/auth_service.py / utils/security.py` |
| `base32_encode_secret()` | `includes/functions.php` | `services/auth_service.py / utils/security.py` |
| `base32_decode_secret()` | `includes/functions.php` | `services/auth_service.py / utils/security.py` |
| `totp_code()` | `includes/functions.php` | `services/auth_service.py / utils/security.py` |
| `verify_totp()` | `includes/functions.php` | `services/auth_service.py / utils/security.py` |
| `encrypt_sensitive()` | `includes/functions.php` | `services/auth_service.py / utils/security.py` |
| `decrypt_sensitive()` | `includes/functions.php` | `services/auth_service.py / utils/security.py` |
| `supported_payment_gateways()` | `includes/functions.php` | `services/billing_service.py` |
| `valid_upi_id()` | `includes/functions.php` | `services/billing_service.py` |
| `normalize_currency()` | `includes/functions.php` | `services/billing_service.py` |
| `payment_gateway_configuration_status()` | `includes/functions.php` | `services/billing_service.py` |
| `payment_method_configuration_status()` | `includes/functions.php` | `services/billing_service.py` |
| `payment_method_audit_snapshot()` | `includes/functions.php` | `services/billing_service.py` |
| `record_payment_method_audit()` | `includes/functions.php` | `services/auth_service.py / services/marketplace_service.py / Flask/Jinja helpers` |
| `active_payment_methods_for_role()` | `includes/functions.php` | `services/billing_service.py` |
| `mfa_secret_from_record()` | `admin/mfa.php` | `services/auth_service.py + routes/admin.py` |

## Important replacement boundaries

- PDO connection singleton → SQLAlchemy engine/session or PyMySQL repository layer; no PHP/PDO runtime remains.
- PHP session globals → Flask session plus the same timeout/version/MFA semantics.
- PHP includes → Jinja template inheritance/includes and imported Python services.
- `header(Location: ...)`/`redirect()` → Flask `redirect(url_for(...))`, while preserving legacy path compatibility.
- PHP CSRF helper → Flask-WTF/CSRFProtect or equivalent secure token validation on state-changing browser forms.
- PHP `mail()` abstraction → configured Python mail provider/SMTP adapter with identical verification/reset behavior.
- cURL Razorpay calls → a Python HTTP client with timeouts/TLS/error classification and the same reconciliation rules.
- Apache `.htaccess` security behavior → Flask/application/deployment controls; `.htaccess` is not a Render dependency.
- PHP upload folders → persistent storage abstraction; Jinja/static URLs must continue rendering the same user-visible images.

## Phase 3 database-layer implementation

The effective database schema is now mapped by Python domain modules while the existing PHP runtime remains untouched during staged migration:

- `models/core.py`: users, locations, categories, platform activity
- `models/marketplace.py`: provider/business profiles, services, requests, reviews, favorites, notifications, reports
- `models/security.py`: schema migrations, auth tokens/rate limits, admin MFA
- `models/billing.py`: plans, subscriptions, payments, payment methods/audit, checkout/webhook/reconciliation, featured listings, lead wallets, advertisements
- `database/schema.sql`: canonical empty-database schema snapshot
- `scripts/init_db.py`: guarded fresh initialization
- `scripts/migrate_db.py`: forward-only existing-database migration execution with checksums
- `scripts/check_db_schema.py`: live table/column/index parity verification
