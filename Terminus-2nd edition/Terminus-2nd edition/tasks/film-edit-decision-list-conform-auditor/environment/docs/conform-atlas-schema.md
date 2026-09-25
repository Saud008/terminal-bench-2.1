# Conform atlas schema

Publish writes JSON with bundle_id, seal_digest, edit_count, diagnostic_count, diagnostics array, and edits array.

Diagnostic categories: df_span_drift, alias_orphan, handle_exceeds_reel, offline_media_note, telecine_pull_drift.

Severity weights live in /app/config/severity-weights.json. Atlases must end with a trailing newline.

Offline media notes include suppressed true when the reel is listed in the missing inventory after alias normalization.
