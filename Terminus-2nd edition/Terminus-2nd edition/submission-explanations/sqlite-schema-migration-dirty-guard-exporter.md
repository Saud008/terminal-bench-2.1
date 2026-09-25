# Submission explanations — sqlite-schema-migration-dirty-guard-exporter

**Task folder:** tasks/sqlite-schema-migration-dirty-guard-exporter/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must implement migratectl apply and export for hospital EHR SQLite cutovers where dirty flags, version bumps, statement splitting, and export locking interact. Fixing only the dirty clear timing can pass rollback counter tests while literal semicolon inserts still fail. Export max version looks easy until versions nine and ten expose string sort bugs. A decoy wrap module sits off the hot path so patching it wastes time. Twenty subprocess tests plus hidden fixture environment overrides catch partial fixes that bundled journals mask.

## Solution Explanation

The oracle replaces apply engine, statement split, SQLite lock, export version, and ingest journal modules then rebuilds migratectl. Apply writes migrate-stage.json only after journal steps update schema_migrations and version_log with post-commit version bumps. Failed up steps keep dirty set until journal down rollbacks finish. Export reads version_log under BEGIN EXCLUSIVE and writes integer max_version into version-ledger.json.

## Verification Explanation

test.sh runs go mod tidy, rebuilds migratectl, and pytest calls the CLI via subprocess on every test. An independent Python reference applier recomputes stage fields and ledger rows from fixtures. Hidden tests vary database suffixes, embedded literal notes, and export hold timing for isolated databases, literal semicolons, and concurrent export locking. NOP on the baseline image scores reward zero. Oracle patches all five solution files and passes twenty of twenty tests.
