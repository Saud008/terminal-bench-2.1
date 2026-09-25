# Submission explanations — ent-schema-edge-migration-rollback-barrier-repair

**Task folder:** tasks/ent-schema-edge-migration-rollback-barrier-repair/
**Platform form only** — not in upload zip.

> Edit in your own words before pasting on the platform form.

## Difficulty Explanation

This task is marked hard because agents must repair four Go modules that drive an ent-style SQLite migration CLI promoting schema version 2 to 3 for the post_author edge. Phase ordering, rollback barrier rules, u:N backfill parsing, and codegen fingerprinting are split across six /app/docs/ contracts, so fixing only PlanDown or only BackfillAuthor still fails bundled up, partial-backfill, or rollback tests. The broken generator runs atlas snapshot before codegen refresh, attaches the FK before backfill and post-validate, and places ent_post_validate after NOT NULL tightening. The broken applier drops idx_posts_author before detaching trg_post_author_edge, backfill ignores the u: prefix on legacy user_ref strings, and codegen refresh returns the stale literal ent-codegen-v2-stale. Agents must rebuild entmigrate after every source edit, and hidden orphan catalogs must abort migrate up even when the bundled path succeeds.

## Solution Explanation

The oracle copies corrected generator.go, applier.go, backfill.go, and refresh.go into /app/internal, rebuilds via verifier-rebuild.sh, and runs a smoke entmigrate up on the bundled catalog. PlanUp interleaves codegen_refresh, atlas_snapshot, hooks, nullable column add, backfill, ent_post_validate, NOT NULL rebuild, edge trigger attach, and index creation exactly as migration-pipeline.md specifies. PlanDown reverses with drop_post_author_fk before drop_author_index so SQLite never blocks index removal while the edge trigger remains. BackfillAuthor maps u:USER_ID refs with substr before falling back to bare numeric user_ref values, and codegen Refresh hashes codegen_seed plus target_version into an eight-byte hex fingerprint. The key insight is that rollback barrier ordering and validate-after-backfill gates are as critical as the DDL statements themselves.

## Verification Explanation

Pytest invokes /usr/local/bin/entmigrate up and down through subprocess after reset-state and verifier-rebuild.sh, then inspects /app/output/migration-report.json and live SQLite state. reference_migrate.py independently computes expected codegen_hash, UP_PHASES event order, and orphan counts so hard-coded report fields fail. Tests cover bundled migrate up and four-step down restoring version 2, first down step detaching the trigger while the index remains, partial-backfill seeds with u:N refs, positive snapshot_seq, and rejection of hidden orphan catalogs including TB3_CATALOG_DIR resolution. Parametrized isolation probes restore broken modules and apply only one golden patch at a time, proving single-file fixes cannot pass full bundled migrate up.
