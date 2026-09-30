# Finding the next elapse

The next elapse after an instant T is the earliest instant after T whose
wall-clock time in the expression's zone matches every field. It is found by
a search over broken-down wall time: year, month, day, hour, minute and
second with microseconds, plus a DST flag that is 0, 1 or "unknown". Fields
may temporarily hold out-of-range values (minute 75, April 31st); converting
the wall time to an instant and back ("folding", see `timezones.md`) rolls
them over into the larger fields.

The search starts from T + 1 µs, broken down in the expression's zone (with
the DST flag of that instant). That starting wall time is kept aside as S for
the stuck check in step 8.

## Rounds

Each round goes through these steps; "restart" means: begin the next round.

0. Fold the working time. Then set its DST flag to "unknown", unless step 8
   has fired earlier in this computation, in which case the flag produced by
   the fold is kept.
1. **Year.** Find the smallest matching year ≥ the current one (below). If
   there is none, the expression never elapses. If the year changed, set the
   date to January 1st and the time to 00:00:00.000000. Then run the bounds
   check; if it reports anything but "exact", or the year is above 2199, the
   expression never elapses.
2. **Month.** Smallest matching month ≥ the current one. If it changed, set
   the day to 1 and the time to midnight. No match, or a bounds check error:
   go to January 1st 00:00:00 of the next year and restart. Bounds check
   "moved": restart.
3. **Day.** Same with the day list. If it changed, set the time to midnight.
   No match or error: go to day 1, 00:00:00 of the next month and restart.
   "Moved": restart.
4. **Weekday.** If weekdays are given and the day (after folding) is not one
   of them, go to 00:00:00 of the next day and restart.
5. **Hour.** If it changed, set minute and second to 0. No match or error:
   go to 00:00:00 of the next day and restart. "Moved": restart (the hour just
   set may not exist on this day because of a clock change).
6. **Minute.** If it changed, set the second to 0. No match or error: go to
   minute 0, second 0 of the next hour and restart. "Moved": restart.
7. **Second** (with microseconds). No match or error: go to second 0 of the
   next minute and restart. "Moved": restart.
8. **Stuck check.** Compare the result with S field by field (year, month,
   day, hour, minute, second, then microseconds). If the result is earlier
   than S, add one hour to it, remember that step 8 fired (see step 0) and
   restart.
9. Convert the working wall time to an instant (with the current DST flag).
   That instant is the elapse.

"Go to" only sets fields; e.g. "next day" increments the day field and lets
the next fold roll it over. After 1000 rounds without a result the
computation fails with `Resource deadlock avoided`.

## Smallest matching value

For the current value v of a field, every element of the field's list offers
a candidate:

* if its start A ≥ v: A;
* otherwise, if it has a repetition R: `A + R·⌈(v − A) / R⌉`, but only if the
  element has no end or the candidate is ≤ its end.

The smallest candidate is the match; it "changed" if it differs from v. `*`
matches v itself. Candidates are not checked against the field's range —
minute 75 or April 31st are left for the bounds check.

## End-of-month days (`~`)

For a `~` day field each element is first turned into day numbers of the
working month. `~k` is the day that lies k − 1 days before the last day of
the month; it is obtained by folding day `1 − k` of the following month and
counts as −1 if the fold lands outside the working month. A missing end
converts to −1 as well. If the converted end is above 0, the converted start
and end are swapped, so the element always runs forward: `~1..3` in a 31-day
month covers days 29 … 31, and in January `~03..07/2` covers 25, 27, 29.
The repetition then counts up from the (possibly swapped) start as above.

## Bounds check

The bounds check folds a copy of the working time and compares it with the
original, field by field from the year down to the second:

* all equal: "exact";
* at the first field that differs, the folded copy's next smaller field is
  reset — year differs: month set to January; month differs: day set to 1;
  day differs: hour set to 0; hour differs: minute set to 0; minute differs:
  second set to 0. Only that one field is reset.
* If the folded copy is earlier than the original, the check fails with an
  error; if it is later, the working time becomes the folded copy (with the
  reset field) and the check reports "moved".

Example: `*:0/25` from 21:51 gives minute 75, which folds to 22:15; the hour
differs, so the minute is reset and the search continues from 22:00, which
matches.

A year above 2199 is an error before anything is folded.
