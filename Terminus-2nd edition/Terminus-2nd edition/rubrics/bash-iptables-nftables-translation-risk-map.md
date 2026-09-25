# Platform rubric — bash-iptables-nftables-translation-risk-map

**Task folder:** tasks/bash-iptables-nftables-translation-risk-map/

Agent implements fw-risk-map ingest staging with iptables and nft tuple NDJSON files plus staging-meta digest, +3
Agent binds chain policy bracket counters on iptables policy lines during ingest, +2
Agent normalizes match extensions with sorted ctstate and multiport dport keys, +2
Agent computes staging_digest from iptables tuples nft tuples and policy precedence rows, +3
Agent records unsupported iptables modules such as recent and limit during ingest scan, +2
Agent implements export that reads staging artifacts only without reopening pair source files, +3
Agent emits translation-risk-report.json with chain_policy_precedence counter_preservation and rule_ordering findings, +3
Agent preserves run_seq stability when re-ingesting an unchanged pair fingerprint, +2
Agent increments run_seq when ingesting a new pair fingerprint, +1
Agent sorts findings by category chain and iptables ordinal in export output, +1
Agent wires export through map_engine risk_engine.py with rebuild in test.sh, +2
Agent fixes only export_report.sh while leaving ingest broken, -3
Agent patches decoy xtables-translate.sh or wrap nft_compat_legacy.awk on the hot path, -3
Agent re-parses iptables-save or nft ruleset files during export after ingest, -5
Agent drops TB3 hidden pair coverage for match normalization traps, -2
Agent weakens staging digest to iptables tuples only excluding nft side, -3
