# Duplicate event timestamps

When multiple events share entity keys, feature, source, and event_ts, retain the row with the greatest seq integer.

Lower seq rows are discarded before point-in-time selection. duplicate_ts_resolved counts discarded rows per run.
