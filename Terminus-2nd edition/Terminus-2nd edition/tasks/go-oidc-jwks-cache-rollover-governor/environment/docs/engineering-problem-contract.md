# Engineering problem — OIDC JWKS cache rollover governance

## Core concept

Identity platform operators reconstruct recorded JWKS timeline transcripts against batched synthetic JWT records to audit verification policy before promoting IdP configuration changes. The engineering problem is temporal key-cache governance for OpenID Connect: case-insensitive kid lookup, issuer and audience binding, cache max-age enforcement in seconds, inclusive stale-key grace windows after rollover, and immediate revoked-key rejection. This is not YARA suppression correlators, ICC softproof gamut drift bundling, Vitess vindex scatter routing, SPIFFE federation atlas diffing, or generic ETL ETL digest repair.

## JWKS pedigree and verification ladder

Each timeline event advances JWKS key pedigree with explicit status movement from active to retired to revoked. Hydration reconstructs the transcript in ascending timeline_mark order, applying every event rather than only the final snapshot. Verification walks a fixed ladder per token: issuer binding, audience binding, revocation short-circuit, active-key cache TTL check, then retired-key grace ladder. Promotion review treats decide-batch output as sealed decision rows; emit-report refuses until hydrate_revision is non-zero.

Kid lookup matches case-insensitively across active then retired pools. Issuer binding compares lowercased trimmed strings. Audience binding requires every token audience entry to appear in policy when policy audiences is non-empty. Cache max-age rejects active-key acceptance when the last timeline mark minus the signature timeline mark exceeds cache_max_age_sec. Grace acceptance uses the retirement timeline mark from the rollover event with inclusive bounds through retired_mark plus grace_window_sec. Revoked kids reject before grace even when the key was previously retired. Keys that leave the active pool may remain verifiable inside the grace ladder until the window closes.

Governance emit seals report_digest over decision_count, decisions sorted by token_id ascending, and scenario after hydration completes.

## Verifier contract

Pytest drives oidcgov as a subprocess and compares CLI output to independent reference math in oidc_verdict_refmath under /tests. Hidden probes under TB3_FIXTURE_DIR exercise grace boundary inclusivity and revoked-during-grace traps with TB3_GRACE_SEC overrides.
