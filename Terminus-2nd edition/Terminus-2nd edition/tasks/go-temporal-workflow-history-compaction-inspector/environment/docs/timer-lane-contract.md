# Timer lane contract

TimerStarted marks a timer pending until TimerFired or TimerCanceled clears it.

Cancelled timers must not count toward pending_timers in replay risk rows.

When TimerFired is present in the ordered history for a timer_id, that timer must leave the pending lane immediately. Fired timers never remain pending in risk rollups, even when an operator sets a timer observation horizon or related grace configuration for diagnostics.
