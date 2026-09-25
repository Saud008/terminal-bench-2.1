# Chronology window lemma

NOTAM rows carry `start_minute` and `end_minute` as integer minute offsets on a wrapping daily axis.

When `end_minute` is greater than or equal to `start_minute`, the window is a plain interval: `eval_minute` is active when it lies at or between `start_minute` and `end_minute` inclusive.

When `end_minute` is less than `start_minute`, the window crosses midnight and wraps: `eval_minute` is active when it is greater than or equal to `start_minute` OR less than or equal to `end_minute`, inclusive on both edges.

Inactive rows must never appear in `active_notams` and must never contribute a closure to the lattice.
