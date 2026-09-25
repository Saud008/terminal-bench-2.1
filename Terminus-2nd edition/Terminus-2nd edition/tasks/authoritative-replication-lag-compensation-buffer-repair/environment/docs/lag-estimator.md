# Lag estimator

simulate writes lag_estimate_us and lag_method into /app/state/sim-report.json.

lag_method must be ewma when the authoritative lag estimator is active.

lag_estimate_us must reflect smoothed RTT tracking across recorded rtt events. A plain arithmetic mean of the same RTT samples produces a different value on the bundled baseline trace.
