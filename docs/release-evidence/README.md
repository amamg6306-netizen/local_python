# Release evidence format

`tools/release_gate.php` deliberately starts **NOT READY**. It only becomes eligible for a controlled live cutover when an authorized operator adds all required evidence files under `storage/release_evidence/` on the deployed environment.

Each file is JSON with no secrets, card data, session IDs or customer data:

```json
{
  "status": "verified",
  "verified_at": "2026-09-24T12:00:00Z",
  "verified_by": "reviewer/team name",
  "reference": "ticket/report/change-id containing the detailed evidence"
}
```

Required filenames: `migration-rehearsal.json`, `backup-restore.json`, `mail-delivery.json`, `sandbox-payment.json`, `performance.json`, `security-review.json`, `legal-financial-review.json`, and `production-smoke.json`.

Do not put API keys, bank credentials, webhook secrets, raw penetration-test secrets or personally identifying test data in these files.
