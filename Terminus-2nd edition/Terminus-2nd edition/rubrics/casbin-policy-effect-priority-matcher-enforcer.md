# Platform rubric — casbin-policy-effect-priority-matcher-enforcer

**Task folder:** tasks/casbin-policy-effect-priority-matcher-enforcer/
**Written:** 2026-07-10T11:05:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent stages policy snapshot with policy and grouping fingerprints before evaluation, +3
Agent selects seed-driven policy bundle subset per casbin-contract bit mask, +3
Agent shuffles merged bundle order with Fisher-Yates from seed digest bytes, +3
Agent applies deny-overrides-allow when allow and deny policies both match, +3
Agent counts every same-priority matcher hit before effect aggregation, +2
Agent evaluates domain-scoped transitive role inheritance for g() matcher, +3
Agent binds audit_digest to snapshot fingerprints and every result row, +3
Agent preserves JSONL request order in enforcement report results, +2
Agent exports bundle list matching snapshot staged bundle order, +2
Agent rebuilds casctl before subprocess enforce verification, +2
Agent passes TB3 hidden seed subset without using bundled config only, +2
Agent treats partial effect fix as sufficient for valid audit witness, -3
Agent ignores deny rules when any allow policy matches, -3
Agent collapses same-priority matches to a single policy hit, -3
Agent omits snapshot staging before writing enforcement report, -3
