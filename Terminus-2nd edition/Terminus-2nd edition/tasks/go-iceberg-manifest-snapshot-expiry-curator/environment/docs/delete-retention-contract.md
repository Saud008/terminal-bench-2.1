# Delete-file retention window

Default delete retention hours come from table.delete_retention_hours unless TB3_DELETE_RETENTION_HOURS overrides.

Given current snapshot event_ms and retention hours H, floor_ms = current_ts - H * 3600 * 1000.

A snapshot is retention-eligible for expiry when event_ms >= floor_ms and the snapshot is not protected.
