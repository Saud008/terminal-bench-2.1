# Time zones and wall-time conversion

Expressions without a zone and expressions marked UTC are evaluated in UTC,
where converting is plain arithmetic. For a named zone the search in
`elapse.md` runs on that zone's wall clock, and every fold converts through
the zone's rules exactly the way the GNU C library (2.36, Debian bookworm)
does it with `mktime(3)` and `localtime(3)`. This file describes that
conversion.

## Zone data

Zones are read from the TZif files under `/usr/share/zoneinfo` (the 64-bit
data block of version 2+ files). Each local time type has a UTC offset and a
DST flag, taken from the file as they are: `Europe/Dublin` flags its winter
time (GMT) as DST and its summer time (IST) as standard time, and some other
zones do similar things.

The local time type at instant t is

* the type of the last transition at or before t;
* before the first transition: the first type that is not DST (the very
  first type if all are DST);
* at or after the last transition: computed from the POSIX TZ rule in the
  file footer (the last transition's type if there is no footer).

### Footer rules

`STD offset [DST [offset],start[/time],end[/time]]`, e.g.
`CET-1CEST,M3.5.0,M10.5.0/3`. Offsets are POSIX style (hours west of
Greenwich, so `-1` is UTC+1); the DST offset defaults to one hour more than
standard time; a transition time defaults to `02:00:00` and may be negative
or beyond 24 hours. Transition dates:

* `Jn` — day n (1 … 365) of the year, February 29th never counted;
* `n` — zero based day n (0 … 365), February 29th counted;
* `Mm.w.d` — weekday d (0 = Sunday) of week w (1 … 5) of month m: start at
  the first such weekday of the month and move forward one week w − 1 times,
  but never past the last day of the month, so `w = 5` means "the last one".

A transition's instant is its local date and time minus the offset in effect
just before it (standard offset for the start of DST, DST offset for its
end), computed for the UTC year of the instant being looked up. DST is in
effect for `start ≤ t < end` when start < end in that year, and for
`t < end or t ≥ start` otherwise (southern hemisphere).

## Converting a wall time to an instant

Input: wall time W (fields may be out of range) with a DST flag f (0, 1 or
unknown), and the conversion hint H in seconds. Every next-elapse
computation starts with H = 0; each successful conversion sets H for the
next one in the same computation (step 5). naive(X) below reads the fields
of a wall time X as if they were UTC, rolling out-of-range fields over.

1. If W's second is below 0 or above 59 it is clamped into 0 … 59 for steps
   2–5 and the difference is added back in step 6.
2. Start probing at `t = naive(W) + H`.
3. Probe: L = local time at t, `d = naive(W) − naive(L)`.
   * d = 0: found, go to step 4.
   * Otherwise, if this probe is at the same instant as the probe two steps
     earlier but not the same as the previous probe (the probes have started
     to alternate between two instants because W falls into a gap), stop here
     with t as the result and go to step 5 — provided that, when f is
     unknown, it is not the case that the previous probe's local time was DST
     and this one's is not; and when f is known, that this probe's DST flag
     differs from f. (With f unknown this settles on the instant whose local
     time is flagged DST when only one of the two is.)
   * Otherwise move to `t + d` and probe again. After six probes without a
     result the conversion fails.
4. If f is known and differs from L's DST flag: for k = 1, 2, … while
   `k × 601200 < 457243209 / 2 + 601200`, look at `t − k × 601200` and then
   `t + k × 601200`; at the first such instant o whose local time Lo has DST
   flag f, the result is `o + naive(W) − naive(Lo)`. If there is none, the
   result is t plus one hour if f = 0, minus one hour if f = 1.
5. H := result − naive(W) (with the clamped second).
6. Add back the second difference from step 1; the folded wall time is the
   local time at the result, carrying that local time's DST flag.

## What this means in practice

* A wall time that exists exactly once converts to that instant.
* A wall time that exists twice (clocks going back) converts to the
  occurrence that H leads to. Within one computation H carries over from the
  previous conversion, and the first conversion starts from the starting
  point's own offset, so a schedule running through the night fires in the
  first pass and does not repeat the doubled hour, while a computation that
  starts inside the second pass stays in it. `*:0/15 Europe/Berlin` from
  2026-10-25 00:10 UTC gives 00:15, 00:30, 00:45, 02:00 UTC; from 01:10 UTC
  it gives 01:15, 01:30, 01:45, 02:00 UTC.
* A wall time inside a gap (clocks going forward) is moved by the size of the
  gap, towards the side flagged DST. For most zones that is forward:
  Berlin's 02:30 on the last Sunday of March becomes 03:30 CEST, the hour
  differs, and a fixed `02:30` schedule skips that day. In `Europe/Dublin`
  the DST side is the winter side, so the move goes backwards; the bounds
  check then reports an error or the stuck check fires (`elapse.md`).
* Zones whose clocks change at midnight (the whole day start is skipped) or
  by 30 minutes go through exactly the same steps; nothing is special-cased.
