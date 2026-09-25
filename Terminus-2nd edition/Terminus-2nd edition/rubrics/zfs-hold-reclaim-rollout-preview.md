# Platform rubric — zfs-hold-reclaim-rollout-preview

**Task folder:** tasks/zfs-hold-reclaim-rollout-preview/
**Written:** 2026-07-16T10:19:08Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent implements zfshold load compile publish on the Bash ZFS reclaim baseline, +3
Agent applies hold-name salt from TB3_HOLD_SALT or config at load time onto snapshot holds, +3
Agent advances load_seq by one when inventory already exists and echoes it in run-meta, +2
Agent blocks snapshots with non-empty holds using blocked_hold before other reasons, +3
Agent blocks clone origin snapshots when any dataset clone_of matches the snapshot name, +3
Agent blocks bookmark targets using the bookmark target field not the bookmark name, +3
Agent fails the pool floor when free_pct is not strictly greater than floor_pct, +3
Agent ranks eligible snapshots by depth desc then creation_txg asc then name asc, +3
Agent publishes audit_digest as sha256 of eligible names joined by newlines in reclaim_rank order, +2
Agent leaves guid_story_helper decoy off the load compile publish hot path, +1
Agent only patches pool_floor while snapshot holds remain ignored, -3
Agent blocks bookmark names instead of bookmark targets, -3
Agent treats free_pct equal to floor_pct as healthy headroom, -3
Agent sorts eligible rows by name only ignoring depth and creation_txg, -3
Agent recomputes gate outcomes inside publish instead of reading reclaim-ledger, -2
