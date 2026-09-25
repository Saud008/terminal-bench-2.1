The typesense-search-cli binary at /usr/local/bin/typesense-search-cli ingests JSONL catalog batches and runs typo-tolerant filtered search against /app/work/index.json. Token dedupe for indexing, typo expansion timing, prefix scoring, docid tie-breaks, brand facet counts, staging snapshots, and search export wiring must align with the contracts in /app/docs/.

Update only the Rust modules listed in /app/docs/repair-scope.md so ingest and search match those contracts. After edits rebuild with bash /app/scripts/rebuild.sh. Ingest must write /app/state/index-staging.json before updating /app/work/index.json.

Use typesense-search-cli index with --index /app/work/index.json and --batch /app/fixtures/documents/<file>.jsonl, and typesense-search-cli search with --index /app/work/index.json, --query <terms>, optional --filter-brand <name>, and --output /app/output/search.json.

Typo tolerance, filter versus rank order, NFC token dedupe, UTF-8 prefix scoring, docid tie-breaks, and facet counting must follow /app/docs/typo-search.md, /app/docs/filter-rank-order.md, /app/docs/token-dedupe.md, /app/docs/docid-tiebreak.md, /app/docs/facet-counts.md, and /app/docs/staging-snapshot.md. Typo edit distance comes from TB3_TYPO_DISTANCE (integer, default 1).

The container has no outbound network access. Run bash /app/scripts/reset-state.sh before local checks. Do not edit /app/docs/, /app/fixtures/, /app/config/, or /tests/.
