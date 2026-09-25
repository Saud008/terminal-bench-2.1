# Delete bitset remap

When compacting multiple segment descriptors, each segment carries delete_bits in local doc id space (0 .. max_doc-1).

Before unioning tombstones into the merged global bitset, remap every local deleted doc id into global space by adding the segment doc offset. The segment doc offset is the sum of max_doc from all prior segments in ingest order.

When TB3_SEGMENT_SEED is set, remap local ids with (local_id + seed) mod max_doc before adding the segment offset.

Union the remapped global ids into a sorted deduplicated delete_bits array. Never insert raw local ids from later segments without offset.
