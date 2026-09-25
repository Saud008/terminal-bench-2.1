# Message stage schema

Files live at /app/work/timeline-ledger/<bag-id>.jsonl. First line is JSON header with bag_id and manifest_revision. Following lines are MsgRow objects with remapped topic names after remap.

After duplicate msg index resolution per /app/docs/duplicate-msg-index-policy.md, MsgRow lines are emitted in global ascending order sorted by (header_stamp_ns, topic) lexicographically. Per-topic header_stamp_ns values must be strictly increasing as required by /app/docs/monotonic-stamp-contract.md.
