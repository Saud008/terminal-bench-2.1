# Platform rubric — ldap-changelog-shadow-sync-cli

**Task folder:** tasks/ldap-changelog-shadow-sync-cli/

# Rubric 1

Agent rebuilds shadow-sync with go build -mod=readonly after editing ingest Go modules, +2
Agent normalizes DN attribute types only while preserving value case, +3
Agent splits RDN on unescaped commas so escaped commas stay inside attribute values, +3
Agent applies LDIF modify operations in file order within each changelog record, +3
Agent skips replayed uSNChanged values without duplicating staging lines, +3
Agent writes last-ingest-stats.json with new_usns and replay_noop counters, +2
Agent fixes whole-string ToLower DN normalization only while modify order stays wrong, -3
Agent patches staging append logic while USN replay still mutates shadow rows, -2

# Rubric 2

Agent exports unique normalized DN counts instead of staging line totals, +3
Agent bumps export_sequence only when preceding ingest recorded new_usns greater than zero, +3
Agent writes shadow.json entries from SQLite shadow without re-applying merge decoy logic, +3
Agent sorts exported entries by normalized_dn for stable JSON output, +2
Agent mirrors replay_stats from last-ingest-stats.json into shadow-audit.json, +2
Agent reports changelog_lines_applied from staging line count not shadow row count, +2
Agent patches export counts while merge/attrs decoy still double-applies modify history, -3
Agent edits merge/attrs.go expecting export output to change without touching export stage, -2
