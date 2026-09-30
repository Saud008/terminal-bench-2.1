# shiftclock CLI

All subcommands take `--zone ZONE`. `ZONE` is either a path to a TZif file or
a zone name such as `America/Santiago`, which is looked up under the directory
in `$SHIFTCLOCK_ZONEINFO` (default `/app/zones`). A path that exists wins over
a name.

Output is one compact JSON object per line (no spaces), keys always in the
order shown. Exit status is 0 on success, 1 on a bad zone file or argument,
2 on usage errors.

## at

    shiftclock at --zone ZONE [--] INSTANT...

`INSTANT` is Unix seconds (may be negative; put `--` before the first
instant in that case) or `YYYY-MM-DDTHH:MM:SSZ`. One line per instant, in
argument order:

    {"utc":"2031-07-01T12:00:00Z","local":"2031-07-01T08:00:00","offset":-14400,"abbr":"EDT","isdst":true}

| key      | meaning                                                   |
|----------|-----------------------------------------------------------|
| `utc`    | the instant, RFC 3339 UTC (see Leap seconds)              |
| `local`  | wall-clock time at that instant, no zone designator       |
| `offset` | UTC offset in seconds, east positive                      |
| `abbr`   | time zone abbreviation, without `<` `>` quoting           |
| `isdst`  | the DST flag of the local time type in effect             |

## transitions

    shiftclock transitions --zone ZONE --from YEAR --to YEAR

Every change of local time type with an instant in
`[YEAR(from)-01-01T00:00:00Z, YEAR(to)+1-01-01T00:00:00Z)`, oldest first.
A change is any difference in offset, abbreviation or DST flag; the listed
values are the ones in effect from that instant on.

    {"at":"2031-11-02T06:00:00Z","offset":-18000,"abbr":"EST","isdst":false}

## Leap seconds

A TZif file may carry leap-second records (the `right/` zone files do). For
such a file every instant counts leap seconds, the way `time_t` does on a
system that runs on those files: a Unix-seconds `INSTANT` is taken as that
count, while `utc`, `local`, `at` and the `YEAR` bounds of `transitions` are
UTC readings obtained through the file's records. An inserted leap second
reads as second 60 (`2016-12-31T23:59:60Z`). A `YYYY-MM-DDTHH:MM:SSZ`
instant is converted the same way, second 60 included. Files without
leap-second records use plain Unix time.

## info

    shiftclock info --zone ZONE

Human-readable dump of the header, the local time types and the footer.
Not meant for parsing.
