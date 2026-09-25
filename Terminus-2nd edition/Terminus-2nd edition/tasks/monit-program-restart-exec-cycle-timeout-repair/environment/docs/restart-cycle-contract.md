# Restart cycle contract

Monit tracks restart cycles per program. A cycle increments only when a start exec transitions the program to running after a scheduled start delay elapses successfully.

Failed start exec attempts (process exits before running) do not consume a restart cycle slot. The export field restart_cycles_used counts only running transitions.

When restart_cycles_used reaches the configured restart limit, further restart requests must be rejected and final_state must be cycle_exhausted.
