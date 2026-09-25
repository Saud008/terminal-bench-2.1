# Compaction watermark planner

Compaction uses watermark_seqno from staging.

An SST file is eligible when max_seqno is less than or equal to watermark_seqno.

Selected file ids are sorted ascending by file_id for export.

Eligibility is independent of size_bytes. Sorting by size_bytes without the watermark filter is not valid selection.
