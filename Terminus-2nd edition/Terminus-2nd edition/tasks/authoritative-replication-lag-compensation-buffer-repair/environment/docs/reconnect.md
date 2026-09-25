# Reconnect rollback window

ROLLBACK_MIN_TICKS is 30. On reconnect, the rollback window must never shrink below ROLLBACK_MIN_TICKS or below the previous window value.

rollback_window_ticks after reconnect is the maximum of the prior window, ROLLBACK_MIN_TICKS, and the reconnect rollback_ticks from the trace event.
