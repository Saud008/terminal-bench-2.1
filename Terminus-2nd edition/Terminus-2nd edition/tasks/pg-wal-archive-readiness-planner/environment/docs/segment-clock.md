# Segment clock

Segment end times for restore target selection come from /app/config/segment-clock.json:

```json
{ "seconds_per_segment": 60, "epoch_start": "2024-06-15 14:30:00 UTC" }
```

segment_end = parse_utc(start_time from staging) + segment_number * seconds_per_segment

Selected segment is the complete WAL file with the greatest segment_end still less than or equal to restore_target.

When TB3_CLOCK_ROOT is set to an absolute directory, load segment-clock.json from that directory instead of /app/config.
