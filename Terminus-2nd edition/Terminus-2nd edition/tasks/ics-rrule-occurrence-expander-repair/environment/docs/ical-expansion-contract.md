# iCalendar expansion contract

```text
expand --ics /app/fixtures/calendars/<name>.ics --window <start>/<end> --db /app/output/<name>.db
```

`--window` uses two RFC3339 UTC instants separated by `/` (inclusive bounds on stored `start_utc`).

Bundled fixture verification windows are listed in `/app/docs/fixture-catalog.md`.

## SQLite output

Table `occurrences`:

| Column | Type | Meaning |
|--------|------|---------|
| `uid` | TEXT | VEVENT `UID` |
| `start_utc` | TEXT | Occurrence instant in RFC3339 UTC |
| `seq` | INTEGER | Zero-based row order after global sort by `start_utc`, then `uid` |

Each run replaces all rows in the database.

## Embedded time zones

Fixture calendars may define `VTIMEZONE` blocks using:

- `X-OFFSET-STANDARD` — standard offset seconds east of UTC (negative for Americas)
- `X-OFFSET-DAYLIGHT` — daylight offset seconds east of UTC
- `X-TRANSITION-TO-DST` — UTC instant when offset switches to daylight
- `X-TRANSITION-TO-STD` — UTC instant when offset returns to standard

`DTSTART;TZID=…` values are local wall times in that zone.

### Spring-forward gap

On the transition to daylight saving (`X-TRANSITION-TO-DST`), one local wall hour does not exist. If a recurrence lands in that gap (for example `02:30` on the skipped hour), **omit** the occurrence entirely. Do not snap it forward to the next valid offset and do not emit a row for it.

Zoned local times in that nonexistent hour must be dropped during UTC conversion.

## Recurrence expansion order

For each `VEVENT`, expansion must follow this order:

1. Generate the raw local series from `RRULE` (`FREQ`, `INTERVAL`, `BYDAY`, `BYSETPOS`, etc.).
2. Union the series with all `RDATE` values, sort, dedupe, then remove every `EXDATE` match. **Always** apply `EXDATE` filtering, including when `RDATE` is present.
3. When `COUNT` is set, keep the first `COUNT` occurrences from the merged list. `COUNT` caps results **after** `EXDATE`/`RDATE` merge, not before.
4. Drop locals after `UNTIL` (`UNTIL` with `Z` compares in UTC; floating `UNTIL` compares in local time and is inclusive on the boundary instant).
5. Convert each remaining local to UTC; skip rows where conversion is omitted (gap suppression).
6. Keep only instants inside the `--window` bounds.
7. Sort all emitted rows globally by `start_utc`, then `uid`, before writing SQLite.

## RRULE details

### Monthly `FREQ=MONTHLY` with `BYSETPOS`

When `RRULE` includes `BYSETPOS` with `FREQ=MONTHLY` (typically together with `BYDAY`):

1. Begin the month walk on **day 1 of `DTSTART`'s calendar month**, keeping `DTSTART`'s local hour/minute/second. Do **not** start the first month on `DTSTART`'s day-of-month.
2. For each month, collect every date in that month that matches `BYDAY`, in ascending date order within the month.
3. Apply `BYSETPOS` to that list. The selected occurrence may fall **on or before `DTSTART`** in the anchor month; include it in the raw series. Do not skip pre-`DTSTART` days when building the month's candidate list.
4. Advance by `INTERVAL` months and repeat.

Example shape: `DTSTART` on the 31st with `BYSETPOS=1` and weekday `BYDAY` still considers every matching weekday from the 1st of that month; the first selected day may precede `DTSTART`.

- `BYSETPOS` uses **1-based** indexing per RFC 5545 (`1` = first matching day in the month, `-1` = last).
- `EXDATE` and `RDATE` values use the same local/UTC interpretation as `DTSTART` in the fixture.

Malformed calendars (unparseable dates or missing required properties) must cause a non-zero exit status.
