# Hook order vs ent validate

ent_pre_validate runs before any author_id backfill. ent_post_validate runs only after backfill_author completes and before set_author_not_null.

The up phase list in PlanUp must interleave hooks with DDL and backfill exactly as migration-pipeline.md specifies. ent_post_validate must not run before backfill_author or before add_author_nullable completes.

The CLI runner calls RunHook once per hook phase in the order returned by PlanUp. Legacy ExecuteHooks batches both validates and must not replace the per-phase runner path.
