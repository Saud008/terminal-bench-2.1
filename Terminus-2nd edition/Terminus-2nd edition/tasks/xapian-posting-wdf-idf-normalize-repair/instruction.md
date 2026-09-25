The xapian-weight-cli binary at /usr/local/bin/xapian-weight-cli indexes JSONL document batches and runs WDF-IDF weighted queries against /app/work/index.json. Posting frequency collection, within-document frequency after positional collapse, collection-frequency accounting, unique-term length normalization, synonym expansion, and OR-branch IDF handling do not match the contracts in /app/docs/.

Repair only the broken Rust modules listed in /app/docs/repair-scope.md. After edits rebuild with bash /app/scripts/rebuild.sh. Ingest must write /app/state/index-staging.json before updating /app/work/index.json; query scoring reads the live index file.

Use xapian-weight-cli index with --index /app/work/index.json and --batch /app/fixtures/documents/<file>.jsonl, and xapian-weight-cli query with --index /app/work/index.json, --query <expression>, and --output /app/output/query.json. Query expressions use AND or OR between lowercase terms; synonym maps on each document line apply during scoring.

Positional collapse, WDF logarithm, collection frequency, length normalization, synonym max-aggregation, and OR-branch IDF must follow /app/docs/xapian-weight.md, /app/docs/token-collapse.md, /app/docs/synonym-policy.md, /app/docs/query-planner.md, and /app/docs/staging-snapshot.md. Rare-term threshold for OR branches is TB3_RARE_CF (integer, default 2).

The container has no outbound network access. Run bash /app/scripts/reset-state.sh before local checks. Do not edit /app/docs/, /app/fixtures/, /app/config/, or /tests/.
