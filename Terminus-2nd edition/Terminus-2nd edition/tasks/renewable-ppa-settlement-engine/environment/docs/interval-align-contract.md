# Interval align contract

Meter reading timestamps in scenario JSON use RFC3339 UTC (ts_utc).

Alignment rule: floor each reading to the nearest lower 15-minute UTC boundary using interval_minutes from the scenario (default 15).

Examples:

- 2026-01-02T12:07:33Z with 15-minute intervals becomes 2026-01-02T12:00:00Z
- 2026-01-02T12:15:00Z stays 2026-01-02T12:15:00Z
- 2026-01-02T12:59:59Z becomes 2026-01-02T12:45:00Z

Seconds and sub-interval remainder truncate downward. Alignment never rounds upward to the next interval.

The aligned interval_start_utc keys market price lookup and settlement line identity.
