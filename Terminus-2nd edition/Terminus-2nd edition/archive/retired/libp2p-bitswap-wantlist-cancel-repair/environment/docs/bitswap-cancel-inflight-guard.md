# Cancel and in-flight guard

When cancel arrives while block_start already ran for the same canonical multihash without block_done, the want must stay reserved until block_done or the in-flight slot clears. Cancel sets a tombstone on the canonical key but must not delete in-flight state.

Ledger credit applies only on block_done, never on block_start. Credit applies at most once per peer and display-cid pair (canonical keys dedupe internally; ledger_totals rows use display CID strings). Every block_done still appends a delivered row even when ledger credit is skipped on a duplicate.

After block_done removes the want, cancel tombstones for that canonical key must not resurrect the want during merge_wants.
