# SEL CSV export format

Path: caller supplies --out (tests use /app/output/sel-events.csv).

## Columns

| Column | Description |
|--------|-------------|
| record_id | Decimal record id |
| timestamp_iso | UTC ISO-8601 seconds precision with Z suffix |
| sensor_type_hex | Uppercase 0x-prefixed sensor type |
| sensor_name | Resolved name from TSV or /app/docs/ipmi-sel.md |
| severity | critical, warning, or info |
| event_type_hex | Uppercase 0x-prefixed lower nibble of event_dir_type |

## Sort order

Rows must be sorted by:

1. severity rank ascending (critical before warning before info)
2. timestamp_iso ascending within the same severity
3. record_id ascending as final tiebreaker

Do not sort by timestamp alone. A later warning must not appear before an earlier critical event.

## Header row

The first line is a header with the column names joined by commas exactly as listed above.
