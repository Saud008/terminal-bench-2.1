# Platform rubric — go-coredump-buildid-symbolization-indexer

**Task folder:** tasks/go-coredump-buildid-symbolization-indexer/

Agent admits coreidx crash evidence with authenticity staging and catalog trust wiring, +3
Agent extracts GNU build-ID notes using little-endian note header layout, +3
Agent authenticates program counters with half-open mmap integrity matching, +3
Agent applies stripped-mapping catalog trust fallback through debug_path, +3
Agent computes duplicate evidence group_key from build_id signal symbol and module basename, +3
Agent writes tamper-evident staging JSONL sorted by timestamp then crash_id, +3
Agent exports sealed SQLite crash_groups and crash_frames tables per schema contract, +3
Agent emits uppercase build_id values in sealed summary JSON groups, +2
Agent honors TB3_CRASH_DIR override for hidden crash bundle admission, +2
Agent ignores internal decoy scalemillis helper outside ingest export hot path, +1
Agent uses inclusive mmap end comparison that mis-resolves boundary PCs, -3
Agent lowercases build_id in SQLite summary export rows, -3
Agent groups duplicates by signal and PC only omitting build_id and symbol, -3
Agent parses ELF note namesz descsz as big-endian on ingest, -3
Agent resolves frames using PC minus file_offset without mmap start subtraction, -3
