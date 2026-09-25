# Export schema

Export subcommand reads /app/state/netifd.snapshot.json only. It must not re-run apply or re-read scenario fixtures.

Output JSON fields:

| Field | Type | Meaning |
|-------|------|---------|
| scenario | string | Scenario name |
| iface | string | Interface name |
| routes | array | Route objects with dst, via, dev, metric |
| addresses | array | Address objects with dev, family, addr |
| pd_leases | array | PD lease objects |
| rules | array | Policy rule objects |
| rules_committed | boolean | True when snapshot was taken after rule commit |
| teardown_log | array | Complete ordered harness event log (see below) |
| route_binding | string | Snapshot digest copied verbatim |

## teardown_log

The complete ordered harness event log: every step name appended by the harness event logger during apply, reload, and teardown, in invocation order. This includes rules_commit during apply rule installation and link_down, link_down_ack, route_del_default during teardown. It is not limited to teardown-phase steps alone.

Route order in export must match the staged snapshot routes array order (no sorting).
