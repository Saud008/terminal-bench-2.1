# Platform rubric — mantidx-rt-killlist-rotate-engine

**Task folder:** tasks/mantidx-rt-killlist-rotate-engine/
**Written:** 2026-07-27T00:00:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent applies killlist to the rotating RAM segment before reassigning docs to disk tier, +3
Agent commits every binlog_pending row during rotate and sets last_committed_seq to max seq, +3
Agent writes rotate-audit with disk_published_before_killlist false and killlist_applied_on_ram_tier true, +2
Agent sets binlog-checkpoint rotate_seq equal to rotate-meta rotate_seq after rotate, +2
Agent rebuilds mantidx with cargo before exercising the CLI, +2
Agent loads batches through TB3_DOCS_DIR absolute paths like bundled fixtures, +2
Agent publishes disk chunks before applying pending killlist during rotate, -3
Agent discards uncommitted binlog_pending rows instead of committing on rotate, -3
Agent scopes rotate killlist application to the newest active_ram segment not other RAM segments, +3
Agent merges pending killlist entries by segment_order then doc_id not doc_id alone, +2
Agent writes killlist-merge-audit merged_order in segment_order then doc_id application order, +2
Agent unions deleted_bitmap from both RAM segments and marks those docs killed during merge-ram, +3
Agent rejects attribute price writes when docs.killed is set and records rejected_killed, +2
Agent excludes killed documents from search-report doc_ids without reviving tombstones, +2
Agent matches search doc_ids to independent reference_hits over the docs table, +2
Agent leaves /app/docs and /app/fixtures unchanged, +1
Agent clears entire killlist pending queue when only one segment rotates, -3
Agent ignores deleted_bitmap when merging RAM segments or updates price on killed docs, -3
