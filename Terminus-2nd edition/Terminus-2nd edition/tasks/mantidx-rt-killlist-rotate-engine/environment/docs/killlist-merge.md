# Killlist merge rules

Pending kill entries carry doc_id, segment_id, and segment_order (registration order of the RAM segment).

During rotate, apply only pending entries whose segment_id matches the RAM segment being published to disk. Pending entries for other RAM segments stay queued until those segments rotate.

When merging pending killlist entries for rotate or RAM consolidation:

- Sort by segment_order ascending, then doc_id ascending.
- Do not sort by doc_id alone; segment registration order decides tombstone precedence when the same doc_id appears in multiple segments.

After all pending entries are applied across rotates, pending is empty and applied is true in killlist.json.

killlist-merge-audit.json schema:

- merged_order: array of objects applied during the latest rotate killlist merge, in application order. Each object has doc_id (integer), segment_id (string), and segment_order (integer). Only entries for the rotating segment appear here.

Delete also marks doc_id in the segment deleted_bitmap inside ram-segments.json.

Delete queues pending killlist entries; documents are marked killed=1 when killlist is applied during rotate (or when merge-ram applies the deleted bitmap on the fixed path).
