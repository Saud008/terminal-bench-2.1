# Platform rubric — pulumi-stack-resource-dependency-export-order

**Task folder:** tasks/pulumi-stack-resource-dependency-export-order/
**Written:** 2026-06-26T00:00:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent validates snapshot version and provider URNs before graph build, +3
Agent builds directed prerequisite adjacency with parent provider and DBR edges, +3
Agent preserves component parent links without flattening children, +3
Agent topologically sorts with snapshot index tie-break not URN strings, +3
Agent places delete-before-replace pairs with old immediately before new, +2
Agent stages dep-ledger.json with epoch and adjacency digest before export, +3
Agent serializes export from ledger resources and adjacency only, +3
Agent increments ledger epoch across repeated order runs without reset, +2
Agent rebuilds pulumi-dep-export with go build before pytest CLI calls, +2
Agent ignores MergeAdjacency decoy helper off export hot path, +1
Agent hardcodes catalog order JSON without running pulumi-dep-export CLI, -3
Agent rebuilds adjacency from snapshot inside export serialization, -3
Agent sorts ready topological queue alphabetically by URN string, -2
Agent rewires component children to grandparent during graph build, -2
Agent skips provider nodes from export order entries, -2
