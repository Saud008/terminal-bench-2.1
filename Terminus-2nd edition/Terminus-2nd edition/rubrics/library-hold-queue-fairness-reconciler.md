# Platform rubric — library-hold-queue-fairness-reconciler

**Task folder:** tasks/library-hold-queue-fairness-reconciler/

Agent loads SQLite scenario databases into active-library.db with scenario metadata sidecar, +2
Agent materializes hold-staging.json with sorted patron digest and catalog seed fingerprint, +3
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
Agent treats suspension end_date as exclusive and serves patrons on last suspended day, -3
Agent reverses FIFO hold_date ordering within the same priority tier, -3
Agent assigns first item copy ignoring pickup branch and interbranch policy, -3
Agent sorts published atlas by copy_id breaking queue_pos contract stability, -3
