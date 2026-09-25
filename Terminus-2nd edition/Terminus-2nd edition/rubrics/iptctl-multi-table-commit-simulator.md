# Platform rubric — iptctl-multi-table-commit-simulator

**Task folder:** tasks/iptctl-multi-table-commit-simulator/

Agent derives phase_config from parsed mangle/nat/filter tables not static literals, +3
Agent resolves kernel commit order from mark visibility lattice when mangle sets and nat matches, +3
Agent implements iptctl ingest with rule_lexer.sh and content-derived phase modules, +2
Agent writes merge-staging sibling with plan_digest and merge_staging_digest binding, +3
Agent implements export_gate.sh validating frozen snapshot without live phase module reads, +3
Agent implements report_emit.sh exporting from staging snapshot only via engine export path, +5
Agent preserves chain policy and per-rule counter suffixes through ingest and export, +2
Agent activates NAT rules only after mangle mark commits per nat_mark_bridge.sh, +2
Agent preserves conntrack rule order after shuffle not alphabetical spec sort, +2
Agent honors seed shuffle of -A lines within each table block during simulation, +2
Agent wires simulate CLI exit status to export exit_code field, +1
Agent patches only report_emit.sh while leaving content-derived phase modules broken, -3
Agent re-parses policy files during export after ingest completed, -5
Agent uses static commit order tokens ignoring parsed mark dependencies, -3
Agent weakens merge-staging digest validation to skip phase_config binding, -2
