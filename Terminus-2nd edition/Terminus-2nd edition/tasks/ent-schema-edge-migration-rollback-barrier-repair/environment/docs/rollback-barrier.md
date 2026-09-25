# Rollback barrier

SQLite keeps the post_author edge barrier active while trg_post_author_edge exists. Dropping idx_posts_author before detaching the trigger raises drop index blocked: edge fk still attached.

Always run drop_post_author_fk before drop_author_index. Full down of four steps returns schema version 2 without author_id column and without idx_posts_author.

After up, a single-step down with --steps 1 must fail if the applier tries index-first ordering.
