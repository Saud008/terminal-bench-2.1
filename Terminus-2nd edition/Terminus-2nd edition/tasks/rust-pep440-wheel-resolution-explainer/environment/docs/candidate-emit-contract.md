# Candidate emit contract

Export writes candidates sorted by package name. Each row includes selected_version, wheel_tag, source_id, and reason.

audit_digest is the lowercase hex encoding of SHA-256 over the compact JSON serialization of the candidates array: no spaces (separators `,` and `:`), object keys in field order `package`, `selected_version`, `wheel_tag`, `source_id`, `reason`. Do not hash pretty-printed JSON or reordered keys.

summary.query_count equals candidates length.

Export reads /app/state/whres-snapshot.json only and must not re-read index files from fixtures.

Verifier cases may write probe outputs under /app/output/ including /app/output/broken-emit.json when testing corrupt snapshot handling.
