# CID canonicalization

Traces use display CIDs: human-readable strings from the fixture registry (for example bafyAA...001 or QmAlias...001). These strings appear in JSONL events and in every staging or export row that contains a cid field.

Canonical multihash hex keys are internal only. internal/cid.CanonicalKey maps a display CID to a 66-character hex key. Dedup, cancel tombstones, in-flight tracking, and priority scheduling compare canonical keys. Canonical hex keys never appear in staging snapshots or pipeline export JSON.

Two display strings that map to the same canonical key represent one block. merge_wants must collapse them to a single want with the highest priority seen. The display CID registered on the first want or merge_wants entry for that canonical key is kept as the want entry display; later alias strings only raise priority.

Registry examples used in fixtures:

bafyAA...001 and QmAlias...001 share canonical key ending in ...0001.

Output row rules (staging and export):

wants_remaining[].cid — display CID from the active want entry (first registration wins on alias merge).

delivered[].cid — display CID from the active want entry at block_done when a want was present; otherwise the block_done event cid string. Alias and merge cases keep the registered display even when block_done names a different alias string for the same block.

ledger_totals[].cid — display CID string (never canonical hex). Credit is recorded on the first block_done for each peer and display-cid pair; the cid value is the display string from that crediting block_done event.

delivered appends one row for every block_done event. Ledger credit applies at most once per peer and display-cid pair even when duplicate block_done events arrive.

wants_remaining sorts by priority descending then cid ascending (display strings).
