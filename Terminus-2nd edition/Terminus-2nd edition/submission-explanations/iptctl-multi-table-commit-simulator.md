# Submission explanations - iptctl-multi-table-commit-simulator

**Task folder:** tasks/iptctl-multi-table-commit-simulator/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-09T12:10:00Z

> Agent scaffold only. Rewrite in your own words before Snorkel upload.

## Difficulty Explanation

This task builds an offline iptables-save commit trace analyzer. I rated it hard because phase_config is not a fixed token list. Ingest must analyze parsed mangle, nat, and filter tables to derive commit order from mark visibility rules, counter preservation modes, and conntrack ordering. Behavior is split across mark-visibility-lattice-contract.md, phase-config-contract.md, export-guard-contract.md, and eight Bash phase modules plus export_gate and report_emit. Fixing one module often passes bundled restores while cross-table mark traps or export-only staging checks still fail. Partial patches that hardcode table order or ignore parsed mark edges look correct on simple fixtures but break NAT activation and kernel-order walks.

## Solution Explanation

The oracle installs corrected phase modules that read parsed table JSON during ingest, golden export_gate and report_emit that validate and export from frozen staging only, and plan_binding plus merge_stage_writer for digest binding. Key insight is that export must trust snapshot bytes and frozen phase_config while ingest derives runtime settings from parsed rule specs per the lattice and phase contracts. The internal simulate.py engine handles report math once staging is correct. Hidden verifier restores require the same content-derived commit order logic as bundled mangle-mark restores.

## Verification Explanation

test.sh runs pytest with 59 behavioral tests. Tests invoke iptctl via subprocess on every run. The iptctl_replay_model module recomputes expected reports from fixtures using independent content-derived phase logic, so agents cannot paste golden JSON. Tests cover ingest staging schema, merge-staging siblings, export guard traps with partial golden patches, hidden cross-table mark restores, and snapshot-only export. Partial-fix traps confirm fixing export alone or one phase module alone still fails other layers. NOP on the broken baseline scores zero. Oracle solve plus rebuild should pass the full suite.
