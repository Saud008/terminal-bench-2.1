# Export schema

| Field | Meaning |
|-------|---------|
| `seed` | decode seed |
| `valid_frame_count` | accepted frames in export (post session/dedup) |
| `checkpoint_frame_count` | frames loaded from checkpoint on resume |
| `deduped_count` | frames skipped as duplicates this run |
| `stale_seq_dropped` | frames dropped by session guard this run |
| `changed_fact_count` | count of rows in `diff_rows` |
| `diff_rows` | decoded fact changes on resume (see below) |
| `routes` | sorted route counts |
| `gps_fixes` | decoded GPS rows |
| `events` | sorted EVENT_LOG rows |

Route entry: `{sysid, compid, msg_id, name, count}`.

Event entry: `{sysid, compid, frame_seq, timestamp_ms, event_seq, value}`.

## Resume fact diffs

When `--resume` is set, compare decoded facts from newly accepted frames in the current input against checkpoint baseline facts for the active `--seed`. Emit one row per changed `(sysid, compid, msg_id, fact_key)` pair.

Diff row fields:

| Field | Meaning |
|-------|---------|
| `sysid` | MAVLink system id |
| `compid` | MAVLink component id |
| `msg_id` | message id |
| `fact_key` | decoded field name (`lat`, `lon`, `time_boot_ms`, `timestamp_ms`, `event_seq`, `value`) |
| `old_value` | prior checkpoint baseline as a stringified JSON scalar |
| `new_value` | new value from the current run as a stringified JSON scalar |

`old_value` and `new_value` must be JSON strings whose contents are valid JSON scalars. Example: integer lat `-111` is exported as the string `"-111"`, not JSON null.

Sort `diff_rows` by `(sysid, compid, msg_id, fact_key)` ascending. Non-resume exports must set `changed_fact_count` to `0` and `diff_rows` to `[]`.

Baseline facts come from checkpoint frames loaded for the active seed before merging new rows. Only facts that differ between baseline and newly accepted frames appear in `diff_rows`.
