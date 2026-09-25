# Platform rubric — bind9-zone-include-fragment-precedence-repair

**Task folder:** tasks/bind9-zone-include-fragment-precedence-repair/
**Written:** 2026-07-04T14:57:36Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent must reconcile include expansion order, record precedence, and digest propagation across multiple shell modules, +5
Agent must preserve ingest to snapshot to export parity while export reads only the saved snapshot state, +3
Agent must keep cache invalidation, SOA reload, wildcard, and NSEC behavior aligned with the contract set, +3
Agent should not need outside DNS infrastructure knowledge beyond the repository contracts, -1
Agent should not spend effort on dependency installation or environment bootstrapping, -1
Agent should not rely on undocumented hidden behavior outside the documented contract surface, -1
