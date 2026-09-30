# Phase 1 Browser / Authorization Test Matrix

Use this matrix on a disposable local database only. The current fresh SQL contains demo data and is destructive.

| ID | Actor | Action | Expected baseline |
|---|---|---|---|
| B01 | Guest | Open homepage/search/provider/business | Public pages render |
| B02 | Guest | Open customer/provider/business/admin dashboards | Redirect/deny according to role gate |
| B03 | Customer | Open provider/business dashboards | 403 |
| B04 | Provider | Open business/admin/customer dashboards | 403 |
| B05 | Business | Open provider profile-management/admin/customer dashboards | 403, except shared available-requirements/request handler intentionally supports provider/business |
| B06 | Admin | Open admin pages | Allowed |
| B07 | Customer A | Open Customer B request ID | 403 |
| B08 | Provider A | Open request assigned to Provider B | 403 unless it is an eligible unclaimed requirement |
| B09 | Customer | POST request/status/review without CSRF | 419/denied |
| B10 | Admin | POST moderation without CSRF | 419/denied |
| B11 | Customer | Review incomplete request | Denied |
| B12 | Customer | Review same completed request twice | Second insert denied by application/unique constraint |
| B13 | Provider/business | Claim same requirement concurrently | At most one assignment succeeds |
| B14 | Blocked account | Reuse prior authenticated session | Session invalidated / login required |
| B15 | Any | Upload PHP/text as image | Rejected by MIME policy |
| B16 | Any | Upload valid >3 MB image | Rejected |
| B17 | Guest | Trigger logout URL | Current baseline logs out via GET; Phase 2 should change this to POST + CSRF |
| B18 | Business | View subscription plans | Current baseline incorrectly shows provider/both audience; known Phase 2 defect |

Do not treat this checklist as executed evidence until results are captured from a configured runtime.
