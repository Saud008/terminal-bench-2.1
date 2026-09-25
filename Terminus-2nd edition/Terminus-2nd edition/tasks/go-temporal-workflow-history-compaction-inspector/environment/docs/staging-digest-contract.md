# Staging digest and projection contract

ingest-history writes /app/state/wf-history-staging.json with a staging_digest computed from the canonical history payload defined in /app/docs/history-staging-schema.md. Digests use /app/fixtures/digest_util.py canonical JSON hashing.

compact-summary writes /app/state/wf-compaction-seal.json with compaction_seal equal to one plus the continue-as-new boundary count.

emit-inspect projects activity rows into /app/output/inspection.db and replay risk rows into /app/output/replay-risk-report.jsonl. Ordering, attempt tracking, timer pending lanes, seal math, SQLite row order, and risk codes must match the contracts cited from /app/docs/.
