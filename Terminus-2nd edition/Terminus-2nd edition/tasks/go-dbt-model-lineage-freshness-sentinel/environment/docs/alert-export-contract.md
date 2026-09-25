# Alert export contract

Alerts array must be sorted by severity rank (error, warn, ok), then alert_code, then subject_id.

Severity ranks: error=0, warn=1, ok=2.

Include SOURCE_STALE alerts for non-ok freshness rows.

Include DISABLED_UPSTREAM alerts per disabled-model-handling.md.

Include EXPOSURE_EMPTY alerts (severity warn) when an exposure's exposure_refs list is empty.

Exact message templates (literal; audit_digest hashes these strings byte-for-byte):

  SOURCE_STALE:      `source stale {minutes_elapsed} min`
  DISABLED_UPSTREAM: `depends on disabled {disabled_upstream_unique_id}`
  EXPOSURE_EMPTY:    `exposure has no model refs`

Examples: `source stale 180 min`, `depends on disabled model.analytics.stg_legacy-a1b2c3d4`.

Do not embed the source unique_id in SOURCE_STALE message text; subject_id already carries it.
Do not use verbose paraphrases such as `enabled model depends on disabled upstream …` or `source … stale 180 minutes`.

audit_digest is sha256 hex over canonical JSON:
{"alerts":...,"exposure_refs":...,"model_order":...,"summary":...}
with sorted keys and no whitespace outside JSON encoding. Verifier contract math uses hashlib sha256 identically.

Each alert object must use field order alert_code, message, severity, subject_id when encoded for audit_digest.
