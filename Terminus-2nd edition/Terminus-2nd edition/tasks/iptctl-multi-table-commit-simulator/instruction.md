Build the iptctl offline iptables-save commit trace analyzer at /app/scripts/iptctl (also /usr/local/bin/iptctl). Operators parse firewall policy bundles, derive mark-visibility lattice and conntrack-ordering phase configuration from parsed mangle/nat/filter table content, materialize merge-staging snapshots, and export multi-table commit trace JSON describing kernel-order walks with NAT mark activation, counter preservation, and conntrack collection modes. This is iptables policy commit analysis, not Count-Min sketch rollup, not ICC color drift, not an iptables-to-nftables translator.

Ingest parses restores through rule_lexer.sh, analyzes parsed tables to resolve phase_config per /app/docs/phase-config-contract.md and /app/docs/mark-visibility-lattice-contract.md, writes staging and merge-staging siblings, and binds plan_digest plus merge_staging_digest. Export validates frozen bindings through export_gate.sh and emits commit trace JSON from snapshot bytes only via the internal engine export path. The export guard checks snapshot coherence only; it is not a proxy for nat_active or conntrack_order field correctness.

Contracts span /app/docs/iptctl-commit-pipeline.md, /app/docs/staging-schema.md, /app/docs/iptables-save-contract.md, /app/docs/export-schema.md, /app/docs/export-guard-contract.md, /app/docs/mark-visibility-lattice-contract.md, and /app/docs/fixture-catalog.md. No single document lists every invariant.

Wire these Bash libraries under /app/lib/: rule_lexer.sh, table_commit_order.sh, chain_policy_mode.sh, rule_counter_mode.sh, nat_mark_bridge.sh, ct_order_mode.sh, plan_binding.sh, merge_stage_writer.sh, export_gate.sh, and report_emit.sh. Export must never reopen raw policy files or consult live module side effects after ingest freezes phase_config.

/app/decoy/legacy-restore-wrapper.sh is a legacy helper outside the iptctl hot path.

Hidden verifier restores live under /opt/verifier-fixtures/tb3-restores/ for cross-table mark ordering traps.

Example:

iptctl simulate --restore /app/fixtures/restores/<name>.v4 --seed <seed> --export /app/output/<name>-<seed>.json

Process exit status must equal the export exit_code field.

Do not edit /app/docs/, /app/fixtures/, /app/tools/, /app/decoy/, or /tests/. Pytest loads tests/iptctl_replay_model.py for independent replay math separate from /app/lib/ behavior. That module may use importlib to load /app/tools/simulate.py when recomputing reports.
