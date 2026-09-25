# Platform rubric — tantivy-segment-delete-bitset-compaction-engine

**Task folder:** tasks/tantivy-segment-delete-bitset-compaction-engine/

Agent remaps local delete bit ids into global doc space before unioning tombstones, +3
Agent subtracts deleted_hits from term freq rows before cross-segment rollup, +3
Agent exports live_max_doc as the sum of segment max_doc values, +2
Agent serializes posting norm values as u8-width JSON numbers in segment-stats.json, +2
Agent keeps second merge export pass idempotent without duplicating delete bits, +3
Agent reads /app/state/tantivy-stage.json in merge export instead of re-ingesting fixtures, +2
Agent rebuilds tantictl with cargo in test.sh after editing merge or export modules, +2
Agent implements doc id permutation when TB3_SEGMENT_SEED is set, +3
Agent leaves src/decoy off the ingest and merge export hot path, +1
Agent ORs local delete bits before applying segment doc offsets, -3
Agent sums raw term freq without tombstone subtraction, -3
Agent exports max single-segment max_doc instead of union doc space, -2
Agent promotes norm integers beyond the u8 field width in exported stats, -2
Agent re-ORs staging delete bits into persisted merge state on pass two, -3
