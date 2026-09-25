# Scenario layout and work paths

Bundled scenario trees ship under:

- /app/fixtures/scenarios/sshd-basic
- /app/fixtures/scenarios/login-nested-include
- /app/fixtures/scenarios/login-nested-include/services/login
- /app/fixtures/scenarios/multi-service-shared
- /app/fixtures/scenarios/substack-nested
- /app/fixtures/scenarios/sudo-wheel

Hidden verifier scenarios ship under /opt/verifier-fixtures/pamtrace/scenarios.

Load metadata for a run id is written to /app/work/{run_id}-load.json (example: /app/work/run-g1-load.json). Re-emit output paths may use names such as /app/output/run-g1-reemit.json. Cross-run scratch roots may use /app/work/tb3-scenario-root when overlaying hidden fixtures.

Optional PAMTRACE_SCENARIO_OVERRIDE selects an alternate scenario tree root whose fixtures/scenarios subtree mirrors the bundled layout.

Rebuild helpers: /app/scripts/rebuild-pamtrace.sh and /app/scripts/reset-state.sh.

Reason codes (ok, requisite_failure, required_failure, sufficient_success) are defined in /app/docs/auth-path-trace-contract.md.
