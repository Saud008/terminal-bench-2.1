# Migration pipeline (ent + atlas)

Schema version 2 ships users and posts with legacy user_ref strings. Version 3 adds the post_author edge on posts.author_id referencing users.id.

Up phases must run in this exact order:

1. codegen_refresh — recompute ent codegen fingerprint from the catalog codegen_seed and target_version.
2. atlas_snapshot — capture atlas diff snapshot only after codegen_refresh produced a non-stale hash.
3. ent_pre_validate — ensure users and posts entities exist.
4. add_author_nullable — add nullable author_id column.
5. backfill_author — map user_ref values into author_id (supports u:N prefix form).
6. ent_post_validate — reject orphan author_id values before constraints tighten.
7. set_author_not_null — rebuild posts with NOT NULL author_id after orphans are zero.
8. add_post_author_fk — attach edge trigger guarding inserts.
9. add_author_index — create idx_posts_author.

Down phases for a full v3 rollback:

1. drop_post_author_fk — detach edge trigger first.
2. drop_author_index — drop idx_posts_author only after FK detached.
3. drop_author_not_null — relax NOT NULL via table rebuild.
4. drop_author_column — remove author_id column restoring v2 shape.

Partial down after a completed up must not leave idx_posts_author while trg_post_author_edge remains.
