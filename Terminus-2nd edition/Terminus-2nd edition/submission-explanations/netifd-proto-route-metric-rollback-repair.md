# Submission explanations — netifd-proto-route-metric-rollback-repair

**Task folder:** tasks/netifd-proto-route-metric-rollback-repair/
**Platform form only** — not in upload zip.

> Edit in your own words before pasting on the platform form.

## Difficulty Explanation

This task is marked hard because agents must repair seven interacting Bash modules that drive a simulated netifd-style veth harness through apply, reload, teardown, and export. Contracts are split across six docs covering proto sequencing, route rollback metrics, hotplug deduplication, IPv6 PD lease release on reload, staging snapshot timing, and export schema integrity. Fixing only proto.sh still fails when teardown runs before link-down ack, when reload leaves duplicate PD leases, or when export reads fixtures instead of the snapshot. Kernel-assigned metrics use config_metric plus kernel_metric_bonus, and rollback must restore that assigned value rather than the bare config field. The route_binding digest binds routes, addresses, leases, rules, and the full harness event log, so partial snapshots or apply-time teardown trips tamper and ordering tests. A hidden reload-metric-trap scenario under TB3_FIXTURES_DIR uses bonus 99 on metric 80, which bundled fixtures alone do not reveal.

## Solution Explanation

The oracle replaces proto.sh, route_rollback.sh, hotplug.sh, pd_lease.sh, state_writer.sh, staging/publish.sh, and export.sh with golden implementations, then runs reset-state.sh. Apply follows the documented sequence: link up, routes with harness-assigned metrics, deduplicated hotplug adds, PD acquire when configured, ip rules commit, then snapshot write without auto-teardown. Reload releases PD leases for the iface, clears routes and addresses without a full reset, and re-runs the apply core. Teardown acknowledges link down before deleting the default route, runs route rollback with stored assigned metrics, and rewrites netifd.snapshot.json so export reflects the post-teardown event log. Export reads only the snapshot, verifies route_binding, preserves staged route order, and emits the complete teardown_log including apply-phase rules_commit entries.

## Verification Explanation

Pytest drives netifd-ctl apply, reload, teardown, and export via subprocess against bundled catalog scenarios and a generated hidden fixture root. reference_netifd.py independently simulates harness state, computes route_binding, and builds expected export JSON so hard-coded outputs fail. Tests cover per-catalog export equality, snapshot persistence after apply, kernel metric 237 after default-route teardown rollback, hotplug burst deduplication, single PD lease after reload, teardown step ordering in the runtime log, rules_committed in snapshot and export, export rejection on tampered route_binding, preserved route array order, hidden reload-metric-trap metric 179, protected fixture and doc checksums, and full teardown_log content after teardown including rules_commit and link_down_ack before route_del_default.
