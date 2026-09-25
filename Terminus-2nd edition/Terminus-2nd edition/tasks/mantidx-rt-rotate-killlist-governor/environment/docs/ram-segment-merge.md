# RAM segment merge

merge-ram combines two RAM segments into the lexicographically smaller segment id.

Rules:

- Docs in either segment deleted_bitmap must remain killed=1 in the merged segment.
- merge-ram-audit.json deleted_respected must be true when merge completes.
- Combined deleted_bitmap is the union of both source bitmaps on the merged segment meta row.

Live docs from both segments are reassigned to merged_into; killed docs stay killed.

When a new insert batch arrives while the active RAM segment already holds documents, mantidx allocates the next ram-N segment for that batch (see rotate-meta.json active_ram).
