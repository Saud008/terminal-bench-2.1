# Phase configuration contract

Phase modules under `/app/lib/` analyze the parsed restore tables produced by `rule_lexer.sh` during **ingest only**. Each module reads `IPT_PARSED_PATH` (intermediate JSON written during ingest) and emits configuration consumed while building the staging snapshot. Export reads the frozen `phase_config` object from the snapshot and must not re-run phase modules.

| Module | Function | Emits |
|--------|----------|-------|
| `table_commit_order.sh` | `lib_phase_a_sequence` | One table name per line in commit order |
| `chain_policy_mode.sh` | `lib_phase_b_policy` | Policy counter mode token |
| `rule_counter_mode.sh` | `lib_phase_c_rules` | Rule counter mode token |
| `nat_mark_bridge.sh` | `lib_phase_d_mark` | Mangle→NAT mark mode token |
| `ct_order_mode.sh` | `lib_phase_e_ct` | Conntrack ordering mode token |

### Analysis rules

Modules must derive tokens from parsed table content and simulation semantics in `/app/docs/iptables-save-contract.md`. Static literals that ignore `IPT_PARSED_PATH` violate this contract.

Commit order must respect mark dependency edges: when a restore contains both mangle `--set-mark` rules and nat `-m mark` matchers, mangle must precede nat in the resolved order. When no such dependency exists, order may follow file discovery order.

Policy and rule counter modes must reflect whether parsed restore lines carry non-zero `[pkts:bytes]` suffixes.

Mark bridge mode must be `linked` only when both mangle set-mark rules and nat mark matchers appear in the same restore.

Conntrack ordering mode must be `chain` when eligible `-m conntrack` rules exist in filter or mangle tables per the eligibility rules in `/app/docs/iptables-save-contract.md`.

Incorrect analysis is frozen into the snapshot at ingest time and affects every export for that snapshot. Export reads frozen tokens only.
