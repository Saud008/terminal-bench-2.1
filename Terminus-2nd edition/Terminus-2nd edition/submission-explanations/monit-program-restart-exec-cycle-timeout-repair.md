# Submission explanations — monit-program-restart-exec-cycle-timeout-repair

**Task folder:** tasks/monit-program-restart-exec-cycle-timeout-repair/
**Platform form only** — not in upload zip.

## Difficulty Explanation

The monitctl harness at /app/bin/monitctl simulates Monit program restart cycles against synthetic monitrc configs and timed exec event scenarios. Agents must repair five Bash policy modules under /app/lib/ while following restart-cycle-contract.md, stop-timeout-driver.md, delay-precedence.md, pidfile-hygiene.md, notify-idfile-order.md, and staging-snapshot.md. The broken baseline defers restarts incorrectly during stop windows, counts failed start attempts toward restart limits, applies start delay on onreboot boots, leaves stale pidfiles after unclean kills, and emits notify lines before the monit id state file updates. Partial fixes that only patch timeout_driver.sh or the decoy check_syntax.sh module still fail bundled catalog scenarios covering cycle caps, combined chains, and notify ordering. Hidden fixtures under /opt/verifier-fixtures/ exercise rapid restart timing and restart-limit exhaustion with different failure modes than bundled cases.

## Solution Explanation

The oracle copies golden_timeout_driver.sh, golden_cycle_counter.sh, golden_delay_precedence.sh, golden_pidfile.sh, and golden_notify.sh into /app/lib/ and validates the library with validate-lib.sh. ingest must write cycle-snapshot.json with program metadata, event counts, and snapshot_sha256 of the scenario bytes. replay consumes the staged snapshot and walks scenario events through the corrected FSM: stop-timeout gating before restart exec, cycle counting only on successful running transitions, zero start delay when onreboot boot is true, pidfile unlink before start after unclean kill, and idfile write before notify emission. Export reports include restart_cycles_used, stop_timeout_respected, notify_before_idfile, pidfile_stale_at_start, final_state, timeline steps, and snapshot_sha256 per cli-surface.md.

## Verification Explanation

test.sh runs pytest with reference_monit.py as an independent Python FSM that recomputes expected replay exports from config and scenario JSON. Tests invoke monitctl ingest and replay via subprocess for six bundled scenario and worker config pairs, comparing key boolean and counter fields plus full timeline and snapshot_sha256. Dedicated reference assertions lock stop-timeout deferral, failed-start cycle accounting, onreboot delay skip, stale pidfile hygiene, and notify ordering semantics. Hidden scenarios hidden-rapid-restart.json and hidden-cycle-cap.json mount under /opt/verifier-fixtures/ and must match reference output without bundled fixture overlap. TB3_SCENARIO_DIR override proves scenario path resolution is not hard-coded to /app/fixtures/scenarios/. Partial-fix traps install broken lib modules with only golden timeout_driver or a patched check_syntax decoy and assert the catalog still fails.
