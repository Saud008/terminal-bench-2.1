# Platform rubric — sled-pagestore-staging-commit-seal-ledger

**Task folder:** tasks/sled-pagestore-staging-commit-seal-ledger/

Agent hashes page registry checksums with 32-bit FNV-1 including generation little-endian bytes, +3
Agent appends ParentPivot split journal records before persisting right child pages, +3
Agent rebalances btree nodes below minimum fanout after deletes via borrow or merge, +3
Agent rebuilds internal high_key from merged children for scan-range pruning, +3
Agent keeps batch apply on staging until publish commits to committed state, +2
Agent makes delete-heavy exports and leaf counts match the reference btree model, +3
Agent returns inclusive scan-range rows that match filtered export after merge-heavy deletes, +3
Agent makes journal replay idempotent on split_seq boundaries, +2
Agent honors snapshot pin files during compaction reclaim, +2
Agent leaves /usr/local/bin/sledtool current after editing policy modules under /app/lib/sled/, +2
Agent implements FNV-1a or omits generation bytes from page checksums, -3
Agent patches leaf merge only without fixing underflow rebalance after deletes, -3
Agent writes RightPage journal entries before ParentPivot or before page persist, -2
Agent leaves stale high_key on internal nodes after merge so scan-range skips valid keys, -3
