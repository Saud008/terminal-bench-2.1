# Staging snapshot

Path: /app/state/wal-archive.stage (or --staging argument)

| Field | Meaning |
|-------|---------|
| staging_version | Must be 1 |
| archive_root | Absolute archive directory |
| start_time | From backup_label UTC |
| start_timeline | From backup_label |
| start_segment_file | WAL file at backup start |
| segments_present | Sorted complete segment filenames uppercase |
| partial_files | Sorted .partial filenames |
| timelines | Array of {timeline, parents[]} from .history files |
| digest | sha256 prefix over sorted segments, timelines, start fields |

Ingest must not write planner output. Plan must load staging from disk and must not rescan the archive for segments_present.
