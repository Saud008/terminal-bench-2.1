# Submission explanations - go-graphql-persisted-query-cache-governor

**Task folder:** tasks/go-graphql-persisted-query-cache-governor/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-09T10:34:22Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

This task is about task identity gql-apq-cache-governor-v1 defines the engineering problem for persisted GraphQL query cache governance. I rated it medium because the behavior is split across audit-export-schema.md, cli-surface.md, engineering-problem-contract.md and multiple source files. Fixing one layer often looks fine on the bundled data while other checks still fail. The painful parts are export must read the on-disk staging snapshot, not re-derive everything from raw inputs and extra probe directories exercise paths the default bundle never hits. With about 18 checks in the suite, a partial fix often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The oracle drops corrected sources (gql_oracle_auditexport.go, gql_oracle_expiryevict.go, gql_oracle_manifestload.go, gql_oracle_schemafit.go) into /app, rebuilds the project, and exercises /app/bin/pqgov against the same fixtures agents see. Ingest validates inputs, writes the staging snapshot and any commit-bind metadata, and only then should export trust those bytes. Key insight: follow the doc contracts for ordering, digests, and exit codes instead of patching around symptoms in one module. Hidden fixture paths must work without special-casing only the bundled data root.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest (18 tests) calls /app/bin/pqgov via subprocess. Tests do not grep source for magic strings. The test module includes its own reference math/parser so expected JSON and side files are recomputed from fixtures, which blocks pasted golden answers. Some cases assert the staging snapshot and manifest bytes before export fields are graded. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
