# TB3 overlay packs

Hidden verifier fixtures may supply alternate manifest packs through TB3_BUNDLE_DIR. The overlay pack tb3-bias-overlay is loaded from tb3-bias-overlay.json inside that directory.

Reference timestamps for the tb3-bias-overlay fixture:

  generated_at 2026-04-01T08:00:00Z
  evaluated_at 2026-04-01T10:00:00Z
  model.analytics.tb3_root last_built_at 2026-04-01T09:00:00Z
  source.analytics.tb3_src loaded_at 2026-04-01T09:40:00Z

Scoped unique ids used by the overlay walk:

  model.analytics.tb3_root
  source.analytics.tb3_src
  exposure.analytics.tb3_view

TB3_FRESHNESS_BIAS_MINUTES adds integer minutes to every freshness row before warn and error classification.

Export output paths use the pattern seed-bundle-freshness-report.json under /app/output. Unknown bundle export attempts use missing-pack and land at paths ending with -missing-pack-freshness-report.json.

Pytest contract math may import hashlib to compute sha256 audit_digest values that must match alert-export-contract.md. The helper script /app/scripts/audit_digest_helper.py imports hashlib for the same canonical JSON digest rules.
