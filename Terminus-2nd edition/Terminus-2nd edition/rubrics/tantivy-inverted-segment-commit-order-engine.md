# Platform rubric — tantivy-inverted-segment-commit-order-engine

**Task folder:** tasks/tantivy-inverted-segment-commit-order-engine/

Agent remaps posting doc ids with segment doc_offset before merge_posting_maps, +3
Agent evicts obsolete staging segment ids from reader_registry during merge, +3
Agent accumulates tombstone ids with doc_offset while merging segments, +3
Agent excludes tombstones when computing pending_live_docs at merge finalize, +3
Agent assigns canonical title=1 and body=2 field norm ids on merged segments, +3
Agent fsyncs WAL marker before commit lock is released, +3
Agent records lock_released_before_fsync false when WAL barrier order is correct, +3
Agent reads committed_segment_ids for search export not staging lanes, +3
Agent omits tombstoned document ids from search hit arrays, +3
Agent keeps stats posting_checksum aligned with merged committed postings, +2
Agent mirrors index-snapshot.json metrics with tantool stats CLI output, +2
Agent honors TB3_INDEX_PREFIX absolute index namespace on ingest and search, +2
Agent keeps dangling_reader_count zero after merge commit publishes, +2
Agent rebuilds tantool via cargo in test.sh after Rust module edits, +2
Agent leaves decoy wrap module outside ingest merge and search hot path, +1
Agent merges raw postings without doc_id offset remap, -3
Agent leaves staging segment ids registered in reader_registry after merge, -3
Agent counts segment doc length ignoring tombstones at finalize, -3
Agent releases commit lock before WAL fsync marker is written, -3
Agent serves search from staging segments or re-tokenizes JSONL fixtures, -3
