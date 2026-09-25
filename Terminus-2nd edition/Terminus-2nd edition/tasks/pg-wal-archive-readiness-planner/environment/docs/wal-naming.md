# PostgreSQL WAL segment naming

Archive files use 24 uppercase hexadecimal characters:

| Positions | Field |
|-----------|-------|
| 1-8 | Timeline ID |
| 9-24 | Log segment number |

Example: 000000010000000000000003 is timeline 1 segment 3.

Partial segments use suffix .partial on the same 24-character base name. Partial files must not appear in segments_present.

Timeline history files are named TTTTTTTT.history where T is eight hex digits. Each history line is: parent_timeline TAB redo_location TAB comment. Parent timeline ids are hexadecimal.

backup_label must exist in the archive root with START TIME, START TIMELINE, and START WAL LOCATION lines per backup-label.md.
