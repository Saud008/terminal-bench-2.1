# Submission explanations — bash-awk-jsonl-windowed-aggregate-repair

**Task folder:** tasks/bash-awk-jsonl-windowed-aggregate-repair/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must wire a three stage awk pipeline where ingest writes staging bytes, the wrapper publishes a ledger manifest, bucket rollups land in an intermediate file, and export validates the manifest before emitting JSON. Bugs are split across ingest dedup and invalid value handling, UTC bucket math, tenant metric key collisions, footer totals, manifest binding, and run sequence persistence. Fixing export alone passes many bundled checks but hidden verifier streams and partial profile tests still fail. Partial wrapper timezone tweaks without ingest epoch fixes also break boundary fixtures. The task needs reading five doc contracts and coordinating five hot path modules plus decoy legacy files.

## Solution Explanation

The oracle copies golden ingest, bucket, and export awk modules plus the golden agg-run wrapper that sets TZ UTC, writes ledger-manifest.json from accepted.ndjson sha256, runs both gawk stages, and updates run-seq.json from a content fingerprint. Ingest must skip duplicate event_id rows and invalid values without coercing zero. Bucket stage must align UTC tumbling windows and separate tenant metric keys. Export must verify manifest events_accepted and digest before writing footer totals from ingest stats.

## Verification Explanation

test.sh runs rebuild-agg.sh then pytest with 27 behavioral tests. Tests call agg-run through subprocess and compare output to an independent Python reference implementation. Staging ledger, manifest digest, bucket rollup lines, and report JSON are checked separately. Two hidden streams under verifier fixtures test manifest trap and dedup first win through the full pipeline. Six partial fix tests swap golden single modules and assert almost correct patches still fail distinct cases. Oracle solution passes all tests and NOP on the broken image scores zero.
