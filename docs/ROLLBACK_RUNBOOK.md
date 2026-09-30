# LocalConnect rollback runbook

1. Disable live payment activation (`PAYMENT_ALLOW_LIVE=false`) before rollback investigation.
2. Capture the failed Render deploy logs and application request IDs; do not delete evidence.
3. If a database migration was applied, use the migration-specific reviewed rollback procedure only when it is safe for current production data. Never restore a database blindly over newer writes.
4. Redeploy the last known-good Git/release version from Render.
5. Keep the same required environment secrets and external MySQL/MariaDB connection settings unless the incident is caused by configuration.
6. If upload storage is implicated, preserve the persistent disk and do not reformat/delete it. Restore from a verified snapshot only after understanding data-loss impact.
7. Verify `/health`, login, role guards, customer request flow, provider/business dashboards, admin access and critical billing state before reopening traffic.
8. If payment webhooks arrived during the incident, reconcile affected payment records before enabling new live payment activity.
9. Document the root cause, affected time window, database/upload changes and the exact release restored.
