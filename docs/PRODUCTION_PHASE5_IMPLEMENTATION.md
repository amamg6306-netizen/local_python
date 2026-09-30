# Production Phase 5 — Performance / Memory / Reliability Implementation

Phase 5 focuses on bounded work, not on claiming an unproven leak. The supplied Phase 4 tree was compared with this tree. Of the 16 selected high-growth listing routes (requests/search/reviews/favorites/portfolio/services/admin lists), 15 had an unbounded `fetchAll()` or, for search, a fixed 100-row cap. In Phase 5 all 16 use a server-bounded page or bounded catalogue read; 0/16 selected high-growth pages buffer an unrestricted result set.

Key implementation decisions:

- Request/search/review/favorite/portfolio/admin pages use `pagination_window()` with a server maximum, request `per + 1` rows, trim one sentinel row, and render previous/next navigation without an extra `COUNT(*)` query.
- High-growth service-request feeds select only rendered fields rather than `r.*`.
- Phase 5 indexes are additive and idempotent where feasible through `information_schema` checks.
- Read-heavy authenticated pages persist a CSRF token and release the PHP session file lock before long database/render work, reducing same-session request serialization without breaking navbar state-changing forms.
- Image re-encoding no longer duplicates the full encoded upload in a PHP string; it uses format-specific GD file decoders and rejects a decode whose conservative working-set estimate would exceed 80% of `memory_limit`.
- Request telemetry is disabled by default and has bounded log rotation.
- Verified webhook processing remains synchronous on the first attempt. If processing fails, a bounded reconciliation queue can recover gateway retries. Queue size, worker batch, retry attempts and backoff are bounded; terminal failures enter `dead` state rather than retrying forever.

Remaining unbounded `fetchAll()` sites after Phase 5 are small/reference/detail contexts (`categories`, service selectors, one request's status/detail data, and admin category management). They are not classified as proven safe for arbitrary growth; Phase 6 should revisit them if product configuration allows those reference sets to become large.
