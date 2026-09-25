# Drain eligibility

Before stale filtering, exclude allocations that are not drain-eligible.

An allocation is ineligible when client_status is down or desired_status is stop.

drain_excluded in summary counts allocations removed by this gate for the compile pass.

Stale suppression and reschedule totals apply only to drain-eligible rows that remain.
