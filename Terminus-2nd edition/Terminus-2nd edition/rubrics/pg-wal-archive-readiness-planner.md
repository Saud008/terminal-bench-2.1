# Platform rubric — pg-wal-archive-readiness-planner

**Task folder:** tasks/pg-wal-archive-readiness-planner/

Agent parses 24-hex WAL segment names with 8-hex timeline and 16-hex segment fields, +3
Agent ingests backup_label START TIME as UTC and writes /app/state/wal-archive.stage, +3
Agent parses timeline history parent ids as hexadecimal not decimal, +2
Agent detects segment continuity gaps when segment numbers are not consecutive, +3
Agent lists partial WAL files separately and excludes them from segments_present, +3
Agent selects restore segment using less-than-or-equal segment end times from staging, +3
Agent builds planner JSON from staging segments_present without rescanning archive directories, +3
Agent rejects restore_ready when partial files block through selected segment, +2
Agent computes staging digest with sorted JSON keys before SHA-256 truncation, +2
Agent honors TB3_CLOCK_ROOT alternate segment-clock.json for hidden archives, +2
Agent leaves legacy_merge decoy off ingest and plan hot paths, +1
Agent patches only WAL name parsing while leaving continuity checks permissive, -3
Agent fixes ingest staging but plan still rescans archive for segment lists, -3
Agent treats partial WAL files as complete segments in segments_present, -2
Agent uses strict less-than restore target comparison at exact segment boundaries, -2
Agent parses timeline history parents as decimal integers, -2
Agent emits restore_ready true on gap archives with missing segments, -2
