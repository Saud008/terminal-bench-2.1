# Rotate metadata

Rotate moves the newest active RAM segment — the last entry in rotate-meta.json active_ram — to a new disk chunk listed in rotate-meta.json.

Required ordering during rotate:

1. Apply pending killlist entries for the active RAM segment only while those documents are still on the ram tier.
2. Publish the RAM segment as a disk chunk (reassign segment_id and tier disk).
3. Commit all binlog pending rows then write binlog-checkpoint.json.

rotate-audit.json records:

- disk_published_before_killlist: must be false when rotate completes successfully.
- killlist_applied: true when pending killlist for the rotating segment was applied during rotate.
- killlist_applied_on_ram_tier: true when every kill applied during rotate happened while the document tier was still ram.
- disk_chunk_id: new disk chunk name (disk-N).
- checkpoint_seq: last committed binlog sequence after rotate.

After rotate, a new RAM segment id is appended to active_ram in rotate-meta.json.
