# Interlock deny-overrides

Beyond lockout-authorization ticket authenticity:

- close_blocked_energized: deny closing a breaker when the target bus is already energized through a different closed path while the procedure marks requires_isolation on that step
- open_parallel_risk: deny opening a breaker that is the only isolation point between an energized source and a de-energized section when parallel_path_guard is true on the step
- out_of_order: step index must match procedure order; skipping indices fails authenticity with reason step_skipped
