# Normalized form

```
[WEEKDAYS ]YEAR-MONTH-DAY HOUR:MINUTE:SECOND[ ZONE]
```

Every field is always written out.

## Elements

Each list element is normalized on its own first:

1. If it has both an end B and a repetition R, the end is lowered to the last
   value actually reached: `B − ((B − A) mod R)`. `0..10/3` becomes
   `00..09/3`.
2. If afterwards `A + R > B` (the repetition can't fire a second time), or if
   `A = B`, the end and the repetition are dropped and only `A` remains.

The elements of a field are then sorted by (start, end, repetition), where a
missing end counts as −1 and a missing repetition as 0, and exact duplicates
are removed.

## Printing a field

* `*` when the field has no restriction. For the second field this is also
  the case whenever one of its elements is "every second from 0" (which is
  what `*` stands for there).
* Otherwise the elements joined by `,`. Start and end values are zero padded
  to 4 digits for the year and 2 digits for every other field; the repetition
  is not padded.
* A range written without a repetition repeats by 1 and prints as `A..B`; a
  repetition of exactly 1 on a range is not printed either (`1..5/1` →
  `01..05`). Other repetitions print as `/R`.
* Seconds print as whole seconds; a start, end or repetition that has a
  fractional part gets `.ffffff` (six digits) appended:
  `00:00:00.5/0.25` → `00:00:00.500000/0.250000`.
* The day field is preceded by `~` instead of `-` for end-of-month
  expressions. If the day field is `*`, the `~` is dropped (`*-*~*` is
  `*-*-*`).

## Weekdays

Printed Monday first. A run of three or more consecutive days is written
`First..Last`, a run of exactly two days `First,Second`, and runs are
separated by `,`:

* `Mon,Tue,Wed,Fri` → `Mon..Wed,Fri`
* `Sun,Sat` → `Sat,Sun`
* `Mon..Tue` → `Mon,Tue`

Nothing is printed (not even the space) when there is no weekday
restriction.

## Zone

` UTC` if the expression is marked UTC, otherwise ` ZONE` exactly as given
if it has a zone, otherwise nothing.
