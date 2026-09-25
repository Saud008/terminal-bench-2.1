# Platform rubric — rust-rosbag-topic-clock-skew-indexer

**Task folder:** tasks/rust-rosbag-topic-clock-skew-indexer/

Agent persists topic_remap table in manifest latch JSON, +3
Agent normalizes messages using header_stamp_ns not receive_stamp_ns, +3
Agent applies canonical topic remap during norm-stream, +3
Agent rejects equal consecutive header_stamp_ns per topic, +3
Agent supersedes duplicate seq rows by highest relay_pass, +3
Agent sorts timeline ledger MsgRows by header_stamp_ns then topic ascending, +2
Agent anchors sync windows on reference topic stamp not global minimum, +3
Agent picks closest in-window match per topic per anchor, +2
Agent computes drift slope via least-squares on sync pair deltas, +3
Agent exports drift_rows without negating slope or intercept, +2
Agent counts sequence gaps in drop_count ledger, +2
Agent writes skew atlas audit_digest over sorted drift topic names, +2
Agent rebuilds skew-cal from /app sources with cargo release locked, +2
Agent honors TB3_BAG_ROOT for hidden bag fixtures, +2
Agent honors TB3_SYNC_WINDOW_NS override during match-sync, +2
Agent leaves topic_remap empty in manifest latch, -3
Agent uses receive_stamp_ns as header_stamp_ns in staging, -3
Agent keeps lower relay_pass on duplicate seq, -2
Agent writes timeline ledger rows in ingest order without global sort, -2
Agent anchors sync pairs to global minimum stamp, -3
Agent negates drift regression slope or intercept, -2
