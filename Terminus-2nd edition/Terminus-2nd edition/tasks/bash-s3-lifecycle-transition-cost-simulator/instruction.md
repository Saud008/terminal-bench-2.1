Implement the s3lc AWS S3 storage charge simulator on the working Bash baseline under /app for the cloud FinOps ledger program. Charge projection applies deterministic calendar-day tier ordering with storage policy precedence, multipart dedupe accounting, and canonical report_digest sealing. Build ingest, simulate, and export workflows that load revision-indexed bucket inventory JSONL, walk tag-scoped storage-class tier schedules with Object Lock billing freezes and unfinished MPU byte accounting, materialize a charge snapshot on disk, and emit a prorated monthly GB-month cost rollup JSON.

Install s3lc at /app/scripts/s3lc and /usr/local/bin/s3lc with these subcommands:

  s3lc ingest --inventory PATH --bucket NAME --staging PATH
  s3lc simulate --staging PATH --rules PATH --holds PATH --window-start YYYY-MM-DD --window-end YYYY-MM-DD
  s3lc cost-report --staging PATH --rates PATH --out PATH
  s3lc export --staging PATH --rates PATH --out PATH

Inventory JSONL field semantics, object revision identity, and delete-marker rows appear in /app/docs/inventory-format.md. Tag-prefix tier rule filters and rule priority tie-breaking appear in /app/docs/rule-precedence.md. Storage-class tier day thresholds, chained STANDARD to IA to GLACIER moves, and expiration timing appear in /app/docs/storage-tier-schedule.md. Delete-marker current-object exclusion and noncurrent expiration appear in /app/docs/delete-marker-semantics.md. Object Lock legal-hold and retention-until billing freezes across all revisions of a key appear in /app/docs/object-lock-billing-freeze.md. Unfinished multipart upload byte totals and completed MPU deduplication appear in /app/docs/multipart-accounting.md. Calendar-month GB-month proration divisors and rate-table lookup appear in /app/docs/gb-month-proration.md. Staging snapshot schema and charge projection block fields appear in /app/docs/staging-schema.md. Monthly charge report sorting and report_digest sealing appear in /app/docs/cost-report-schema.md.

simulate writes the charge projection block into the staging file beside inventory_fingerprint. cost-report and export refuse to run until simulation.window_end is present. Export reads inventory, rules, and holds paths from TB3_INVENTORY_FILE, TB3_RULES_FILE, and TB3_HOLDS_FILE per verifier contract. Digest sealing contracts appear in /app/docs/staging-schema.md and /app/docs/cost-report-schema.md.

Bundled fixtures live under /app/fixtures/ with bucket name finops-ledger in /app/config/s3lc.json. Hidden verifier fixtures live under /opt/verifier-fixtures/s3lc_hidden. Run /app/scripts/reset-state.sh before cross-run verifier cases. The decoy storage_class_sorter helper under /app/lib/decoy is not used by ingest, simulate, or cost-report.

Tests invoke s3lc through subprocess after /app/scripts/rebuild-s3lc.sh and compare results to s3lc_verifier_oracle.py contract math. Hardcoding report JSON is insufficient.
