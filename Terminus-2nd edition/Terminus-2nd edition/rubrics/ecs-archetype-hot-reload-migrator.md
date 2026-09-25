# Platform rubric — ecs-archetype-hot-reload-migrator

**Task folder:** tasks/ecs-archetype-hot-reload-migrator/
**Written:** 2026-07-27T00:00:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

# Rubric 1

Agent rebuilds ecs-migrate with cargo build --locked from /app after editing ecs-core sources, +1
Agent rebuilds archetypes from live chunk payload bytes not stale SQLite columns, +3
Agent assigns archetype_id before remapping placeholder stable_id zero rows, +3
Agent remaps stable_id zero using rowid updates while skipping tombstoned ids, +3
Agent resumes migration from journal commit_cursor without re-running step one, +2
Agent moves entities across chunks per layout migration move step, +2
Agent writes chunk checksums using big-endian header plus payload per chunk-format.md, +2
Agent marks replay journal committed with correct commit_cursor after apply, +2
Agent keeps double apply idempotent with empty steps_applied on committed journal, +2
Agent keeps public ecs-core functions listed in module-contracts.md with unchanged signatures, +1
Agent hardcodes migration-report.json without running ecs-migrate apply, -3
Agent remaps placeholder stable_id onto tombstoned id 42, -3
Agent rebuilds archetypes using SQLite stable_id parity instead of chunk payloads, -2
Agent updates stable_id zero rows with stable_id equality predicate affecting all placeholders, -2
Agent ignores journal replay cursor and re-applies completed migration steps, -2
