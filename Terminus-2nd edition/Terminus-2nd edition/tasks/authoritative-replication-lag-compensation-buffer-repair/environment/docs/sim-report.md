# Simulation report

simulate writes /app/state/sim-report.json with lag_estimate_us, lag_method, buffered_inputs_applied, duplicate_inputs_skipped, late_frames_rejected, read_head, rollback_window_ticks, and tick_rate_hz.

lag_method must be ewma when the EWMA estimator from lag-estimator.md is active.

When TB3_TRACE_DIR is set to an absolute directory, simulate may pass only the trace filename; the path resolves under that directory.
