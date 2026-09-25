# Platform rubric — netlink-rtnl-multipath-topology-witness

**Task folder:** tasks/netlink-rtnl-multipath-topology-witness/
**Written:** 2026-07-08T14:32:46Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent implements nlctl decode against cited /app/docs contracts for catalog dumps, +5
Agent writes aligned bind and NH staging artifacts under /app/state before export, +3
Agent computes export_digest from NH snapshot fields per export-digest-schema.md, +3
Agent preserves multipath weight scaling and per-route nexthop id restart rules, +2
Agent formats IPv6 gateways per nexthop-bind-contract textual rules, +2
Agent keeps decode exit codes correct for missing dumps and bad usage, +1
Agent edits protected docs, fixtures, or shared model/attr/lib entry points, -3
Agent hardcodes export JSON without following dump binary path, -3
Agent leaves staging snapshots inconsistent with export_digest, -2
Agent claims success after fixing only one pipeline stage, -2
