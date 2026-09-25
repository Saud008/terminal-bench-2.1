# CLI surface

monitctl ingest --config PATH --scenario PATH writes /app/state/cycle-snapshot.json with normalized program config, scenario name, event count, and snapshot_sha256 of the scenario bytes.

monitctl replay --config PATH --scenario PATH --export PATH runs the fixed replay driver in /app/tools/run_replay.py. Policy hooks are implemented in /app/lib/*.sh and are sourced for each decision. The export JSON uses fields program, restart_cycles_used, stop_timeout_respected, notify_before_idfile, pidfile_stale_at_start, final_state, timeline (array of step records), and snapshot_sha256 copied from ingest when present.

TB3_SCENARIO_DIR when set to an absolute directory replaces /app/fixtures/scenarios for scenario basename lookup. Absolute --scenario paths are used as given. Config JSON paths remain explicit arguments.

Agents repair /app/lib/ only. Do not modify /app/tools/run_replay.py.
