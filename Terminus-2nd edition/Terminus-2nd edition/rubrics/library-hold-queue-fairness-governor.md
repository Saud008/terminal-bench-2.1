# Platform rubric — library-hold-queue-fairness-governor

**Task folder:** tasks/library-hold-queue-fairness-governor/
**Form category:** System Administration (zip `system-administration`; host-local holdfairctl admit → gate → seal)
**Written:** 2026-07-29T15:20:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent loads SQLite scenario databases into active-library.db with scenario metadata sidecar, +2
Agent materializes hold-queue-rollup.json with patron digest and request_id-ordered hold pairs per hold-rollup contract, +3
Agent skips hold requests for patrons inside inclusive suspension start through end dates, +3
Agent orders eligible holds by priority rank ascending then hold_date ascending then patron_id, +3
Agent selects available copy at pickup branch before interbranch transfer candidates, +3
Agent refuses copies whose status is not exactly available including on_shelf decoy rows, +3
Agent computes run_stamp from staging digest plus scenario name for idempotent reconcile, +2
Agent increments reconcile_pass only after reconcile-fairness writes reconcile-log.json, +2
Agent blocks publish-atlas until reconcile_pass is greater than zero, +2
Agent sorts assignment atlas rows by queue_pos then patron_id for stable export, +2
Agent honors TB3 reconcile date override on hidden suspension boundary trap scenario, +2
Agent rebuilds holdfairctl via verifier-rebuild.sh before subprocess CLI verification, +2
Agent leaves /app/docs and /app/fixtures unchanged, +1
Agent treats suspension end_date as exclusive and serves patrons on last suspended day, -3
Agent reverses FIFO hold_date ordering within the same priority tier, -3
Agent assigns first item copy ignoring pickup branch and interbranch policy, -3
Agent sorts published atlas by copy_id breaking queue_pos contract stability, -3
Agent edits /app/docs or /app/fixtures to shortcut verification, -3
Agent copies oracle patches from /solution mount instead of repairing holdfairctl modules, -3
