# Staging snapshot contract

Path: /app/state/netifd.snapshot.json

Written after ip rules are committed on apply, and rewritten after a successful teardown subcommand completes its ordered actions.

Fields mirror export payload plus route_binding and schema version 1.

## teardown_log

Same definition as /app/docs/export-schema.md: the complete ordered harness event log, not teardown-phase names only.

## route_binding

Lowercase SHA-256 hex over UTF-8 newline-joined parts in order:

1. scenario name
2. iface
3. compact JSON array of routes in harness order
4. compact JSON array of addresses in harness order
5. compact JSON array of pd_leases in harness order
6. compact JSON array of rules in harness order
7. compact JSON array of teardown_log strings in order

Export must recompute route_binding from the snapshot and reject mismatches.
