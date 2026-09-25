# EXIF timestamp normalization

Each capture row provides timestamp_raw (ISO-8601 wall clock without timezone) and timestamp_tz (integer minutes offset from UTC to local; US Eastern is -300).

Normalized UTC milliseconds:

```
normalized_ms = parse_utc_ms(timestamp_raw) - (timestamp_tz * 60000)
```

parse_utc_ms treats timestamp_raw components as UTC when converting to unix milliseconds.

Align and digest stages must use normalized_ms for ordering and lens profile effective_capture_ms selection.
