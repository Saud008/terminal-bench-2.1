# tickwheel command line

```
tickwheel calendar [--base-time=TIME] [--iterations=N] EXPRESSION...
```

`tickwheel calendar` is a drop-in for `systemd-analyze calendar` as shipped
with systemd 252 (Debian bookworm, 252.39), run with `TZ=UTC`. Each
EXPRESSION is one calendar event in `OnCalendar=` syntax (see `syntax.md`).
The only intended differences from systemd's output are listed at the end of
this file.

## Options

`--base-time=TIME`
: Instant the elapses are counted from. Accepted forms are `@SECONDS`,
  `YYYY-MM-DD`, `YYYY-MM-DD HH:MM` and `YYYY-MM-DD HH:MM:SS`, each optionally
  followed by ` UTC`; all of them are UTC. Defaults to the current time. The
  same base is used for every EXPRESSION.

`--iterations=N`
: Number of elapses to print per expression (default 1).

Both options also accept their value as the following argument
(`--iterations 5`). `--` ends option processing.

## Report

For every expression tickwheel prints a table:

```
  Original form: *:0/20
Normalized form: *-*-* *:00/20:00
    Next elapse: Sat 2026-03-28 12:20:00 UTC
       Iter. #2: Sat 2026-03-28 12:40:00 UTC
       Iter. #3: Sat 2026-03-28 13:00:00 UTC
```

* `Original form:` is only present when the expression text differs from the
  normalized form (plain string comparison). The normalized form is described
  in `normalization.md`.
* `Next elapse:` is the first elapse strictly after the base time;
  `Iter. #k:` is the first elapse strictly after the one in the row above.
  Each row is an independent next-elapse computation (`elapse.md`).
* Timestamps are always printed in UTC as `Www YYYY-MM-DD HH:MM:SS UTC`,
  whatever zone the expression uses. Fractions of a second are not printed.
* If there is no elapse after the base at all, the only elapse row is
  `Next elapse: never`. If the elapses run out after fewer than N rows, the
  table just ends there.
* Labels are right-aligned to the longest label in the same table, followed
  by a single space and the value. Lines have no trailing white space.

Tables for consecutive expressions are separated by one empty line. The
separator is written after every expression except the last one, including
after an expression that failed.

## Errors

If an expression cannot be parsed, nothing is written to standard output for
it and standard error gets

```
Failed to parse calendar specification 'EXPRESSION': REASON
```

REASON is `Invalid argument` for syntax and range errors,
`Numerical result out of range` for numbers above 2147483647 (in the second
field: more than 2147483647 microseconds) and for a zero repetition (`/0`),
and `No buffer space available` when a field has more
than 241 list elements.

If computing an elapse fails for a reason other than "never" (for example the
search giving up, see `elapse.md`), standard error gets

```
Failed to determine next elapse for 'EXPRESSION': REASON
```

and the table for that expression is not printed at all, not even the rows
computed before the failure.

The exit status is 0 when every expression succeeded, 1 when at least one
expression failed and 2 for command-line usage errors.

## Differences from systemd-analyze

* No `From now:` rows.
* No `(in UTC):` rows (they are never printed under `TZ=UTC` anyway).
* No hint lines after parse errors.
