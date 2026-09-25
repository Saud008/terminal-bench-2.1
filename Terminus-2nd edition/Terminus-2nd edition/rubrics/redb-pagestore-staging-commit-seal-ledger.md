# Platform rubric - redb-pagestore-staging-commit-seal-ledger

**Task folder:** tasks/redb-pagestore-staging-commit-seal-ledger/

Agent keeps batch apply on staging until commit publishes committed tables, +3
Agent splits leaves and internals with mid = n / 2 floor median, +3
Agent borrows from the left sibling first on underflow before borrowing right, +3
Agent merges underflowing children and propagates underflow to the parent, +3
Agent flushes child page payloads before recording root_height on commit, +3
Agent writes btree-snapshot.json fields that match walk metrics after commit, +2
Agent exports sealed key/value rows from committed tables only, +3
Agent makes delete-heavy and replay exports match the reference btree model, +3
Agent rebuilds redbtool with cargo build after editing Rust engine sources, +2
Agent mutates committed export state during batch before commit, -3
Agent uses ceil(n/2) left medians so repeated splits disorder keys, -3
Agent borrows from the right sibling while a left donor still has spare keys, -2
Agent records root_height while children_fsynced is still false, -3
Agent lets export scan staging.json before commit, -3
