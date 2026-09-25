# Fixture catalog

| Calendar | Role | Verification `--window` |
|----------|------|-------------------------|
| `weekly-byday.ics` | Weekly recurrence with zone conversion | `2024-01-01T00:00:00Z/2024-02-29T23:59:59Z` |
| `monthly-setpos.ics` | Monthly recurrence with `BYSETPOS` | `2024-01-01T00:00:00Z/2024-04-30T23:59:59Z` |
| `negative-setpos.ics` | Monthly `BYSETPOS=-1` (last matching weekday) | `2024-01-01T00:00:00Z/2024-04-30T23:59:59Z` |
| `exdate-rdate.ics` | `EXDATE` with `RDATE` present | `2024-01-01T00:00:00Z/2024-02-29T23:59:59Z` |
| `exdate-on-rdate.ics` | `EXDATE` targets the same local time as `RDATE` | `2024-01-01T00:00:00Z/2024-02-29T23:59:59Z` |
| `count-exdate.ics` | `COUNT` after `EXDATE` removal | `2024-01-01T00:00:00Z/2024-03-31T23:59:59Z` |
| `until-floating.ics` | Floating `UNTIL` boundary (inclusive) | `2024-01-01T00:00:00Z/2024-03-31T23:59:59Z` |
| `until-utc.ics` | `UNTIL` with `Z` suffix (UTC comparison) | `2024-01-01T00:00:00Z/2024-03-31T23:59:59Z` |
| `interval-biweekly.ics` | `FREQ=WEEKLY` with `INTERVAL=2` | `2024-01-01T00:00:00Z/2024-03-31T23:59:59Z` |
| `dst-spring.ics` | Spring-forward gap suppression | `2024-03-01T00:00:00Z/2024-04-30T23:59:59Z` |
| `malformed.ics` | Invalid input | any valid window (must fail) |

`dst-spring.ics` uses weekly `02:30` local times across the US spring-forward transition; the occurrence in the nonexistent gap must not appear in output.

`count-exdate.ics` uses `COUNT=5` with one `EXDATE`; output must contain five rows after the exception is removed from the merged series.

`exdate-on-rdate.ics` must not emit a row for the shared `EXDATE`/`RDATE` local instant even though `RDATE` re-injects that time after series generation.
