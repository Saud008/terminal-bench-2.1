# Calendar event syntax

```
[WEEKDAYS] [DATE] [TIME] [ZONE]
```

Parts are separated by one or more spaces. At least one of WEEKDAYS, DATE
and TIME has to be present. An omitted DATE means `*-*-*`; an omitted TIME
means `00:00:00`.

## Shorthands

The whole expression (apart from a zone suffix) may be one of these words,
in any letter case:

| word | meaning |
|---|---|
| `minutely` | `*-*-* *:*:00` |
| `hourly` | `*-*-* *:00:00` |
| `daily` | `*-*-* 00:00:00` |
| `monthly` | `*-*-01 00:00:00` |
| `weekly` | `Mon *-*-* 00:00:00` |
| `yearly`, `annually`, `anually` | `*-01-01 00:00:00` |
| `quarterly` | `*-01,04,07,10-01 00:00:00` |
| `semiannually`, `semi-annually`, `biannually`, `bi-annually` | `*-01,07-01 00:00:00` |

## Zone suffix

1. If the expression ends in a space followed by `UTC` (any letter case), it
   is evaluated in UTC and marked as UTC.
2. Otherwise, if the text after the last space is a valid zone name, the
   expression is evaluated in that zone. A zone name is valid if it is exactly
   `UTC`, or if it uses only ASCII letters, digits, `-`, `_`, `+` and `/`,
   does not start or end with `/`, contains no `//`, and names a regular file
   under `/usr/share/zoneinfo` whose first four bytes are `TZif`. Names are
   case-sensitive; a word that is not a zone simply stays part of the
   expression (which usually makes it fail to parse).
3. Otherwise the expression is evaluated in UTC without being marked.

A zone named exactly `UTC` is treated like case 1.

## Weekdays

`Monday` … `Sunday` or `Mon` … `Sun`, in any letter case. A day name must be
followed by the end of the expression, a space, `,`, `.` or `-`.

* `A,B` lists days, `A..B` (or `A-B`, kept for compatibility) is a range.
* A range must go forward inside the week, which starts on Monday: `Mon..Fri`
  is fine, `Fri..Mon` is invalid. Ranges don't wrap around the weekend.
* A range can't be continued (`Mon..Wed..Fri`) or left open (`Mon..`).
* A trailing comma is accepted (`Sat,Sun,`).

A weekday list that ends up selecting no day or all seven days places no
restriction. If weekdays are given, a day has to match the weekday list
**and** the date part.

## Date

`YEAR-MONTH-DAY` or `MONTH-DAY`. Each field is `*` or a list (below).

* Writing `~` instead of the `-` in front of the day counts days from the end
  of the month: `~1` is the last day of the month, `~2` the one before it,
  and so on (details in `elapse.md`). `~` is only allowed in front of the day.
* Years are 1970 … 2199. A year value below 70 means 20xx and a value from
  70 to 99 means 19xx (so `99-12-31` is 1999-12-31 and `05` is 2005); this is
  applied to range ends as well.
* `@SECONDS` stands for one single second (UTC). It replaces the date *and*
  the time; nothing but a zone suffix may follow it. It is normalized to the
  fixed `YYYY-MM-DD HH:MM:SS UTC`.

## Time

`HOUR:MINUTE` or `HOUR:MINUTE:SECOND`; a missing second means `00`.

The second may carry a fraction of up to six digits (microseconds). A
seventh digit of 5 … 9 rounds the sixth digit up; any digits after that are
ignored. `*` in the second field means every whole second.

## Lists, ranges and repetitions

Every date and time field is either `*` (no restriction) or a comma separated
list of elements:

| element | values |
|---|---|
| `N` | N |
| `A..B` | A, A+1, …, B |
| `A/R` | A, A+R, A+2R, … up to the end of the field's range |
| `A..B/R` | A, A+R, A+2R, … not beyond B |

Numbers are plain decimal digits, leading zeros allowed. `*` cannot be
combined with anything: `*/5` is invalid, write `0/5`. A repetition of `0`
is an error (`Numerical result out of range`). Seconds may use fractions in
A, B and R; a seconds range without an explicit repetition has to cover at
least one second.

## Validity

After normalization (`normalization.md`) every element has to satisfy, with
MIN … MAX being year 1970 … 2199, month 1 … 12, day 1 … 31, hour 0 … 23,
minute 0 … 59, second 0 … 59.999999:

* MIN ≤ A ≤ MAX and R ≤ MAX − MIN;
* with an end: MIN ≤ B ≤ MAX and A + R ≤ B;
* without an end: A + R ≤ MAX (so `*:50/10` is invalid).

For `~` days MAX is 28 instead of 31 and, without an end, A − R ≥ 1 replaces
A + R ≤ MAX.

Anything else that doesn't fit the grammar is `Invalid argument`.
