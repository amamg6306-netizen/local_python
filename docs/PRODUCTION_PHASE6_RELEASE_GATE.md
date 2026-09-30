# Phase 6 release gate

`php tools/release_gate.php` must be treated as a minimum operational gate, not a substitute for human review. It requires hardened production configuration, required PHP extensions, enabled production mail, no demo/destructive production seed, and eight external evidence records. The safe pre-live state keeps `PAYMENT_ALLOW_LIVE=false`; if every other gate passes, the tool reports readiness for controlled live enablement rather than requiring the flag to be switched early.

The artifact ships without those external evidence records, therefore the expected packaged status is **NOT_READY_FOR_LIVE_PAYMENTS**. `PAYMENT_ALLOW_LIVE=false` remains the intentional safe pre-live setting; once all other gates pass, the release gate can report readiness for controlled live enablement while the flag is still false.

A reviewer must not create evidence files just to silence the gate. Each `reference` must point to actual retained evidence such as a CI run, staging test report, penetration-test report, approved legal review or change ticket. Evidence JSON must contain no secrets or personal/payment data.
