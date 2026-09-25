# SQLite export schema

Database path: `/app/output/crash_index.sqlite`

## crash_groups

| Column | Type | Notes |
|--------|------|-------|
| group_key | TEXT PRIMARY KEY | Dedupe key |
| signal | INTEGER | Signal number |
| build_id | TEXT | Uppercase hex |
| top_symbol | TEXT | Top frame symbol |
| crash_count | INTEGER | Member crashes |

## crash_frames

| Column | Type | Notes |
|--------|------|-------|
| crash_id | TEXT | |
| group_key | TEXT | FK to crash_groups |
| frame_index | INTEGER | 0-based |
| pc | TEXT | Original pc hex |
| symbol | TEXT | Resolved symbol or empty |
| module | TEXT | Module basename |

Rows in crash_frames sorted by crash_id, frame_index when exported to summary.
