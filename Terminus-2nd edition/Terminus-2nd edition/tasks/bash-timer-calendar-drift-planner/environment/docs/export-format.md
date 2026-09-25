# Export format

drift-report.json fields:

- timer_name
- timer_mode calendar, monotonic, or mixed
- timezone_normalized effective timezone string
- next_fire_utc_earliest
- next_fire_utc_latest
- missed_run_count
- missed_run_utc sorted ascending ISO8601 Z
- catchup_run_count
- catchup_run_utc sorted ascending ISO8601 Z
- randomized_delay_sec
- accuracy_sec
- drop_in_overrides_applied
- persistent_enabled
- plan_digest sha256 hex of compact JSON containing timer_name, timer_mode, next fire bounds, missed_run_utc, catchup_run_utc

JSON keys sorted with compact separators and trailing newline.
