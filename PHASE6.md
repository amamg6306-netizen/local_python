# LocalConnect Phase 6

Phase 6 extends the combined Phase 1–5 application with monetization architecture.

Implemented: database-backed Free/Professional/Business plan catalogue; active user subscriptions; provider/business subscription screens; payment ledger and admin revenue view; featured-listing schema; lead-credit wallet schema; admin advertisement creation/listing; advertisement budget/impression/click fields; and payment-gateway-ready records without processing real money.

## Existing database upgrade
Import `database/phase6_migration.sql` once after Phase 5.

## Payment integration later
Do not place gateway secrets in source files. Add environment/config values in a dedicated payment configuration file, create server-side order/payment verification endpoints, and only mark `payments.status='paid'` after cryptographic gateway verification. The current UI deliberately disables paid upgrades until that integration exists.
