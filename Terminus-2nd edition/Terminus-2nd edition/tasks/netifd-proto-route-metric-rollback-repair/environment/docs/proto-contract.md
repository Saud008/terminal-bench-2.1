# Proto handler contract

The netifd-ctl apply subcommand drives the simulated veth proto handler for one fixture scenario JSON file.

## Apply sequence

On apply, in order:

1. Reset harness runtime state.
2. Bring the scenario iface link up.
3. Install configured routes using kernel-assigned metrics (config_metric + kernel_metric_bonus recorded in harness).
4. Process hotplug events (see /app/docs/hotplug-contract.md).
5. Acquire IPv6 PD lease when pd_prefix is present (see /app/docs/pd-lease-contract.md).
6. Install ip rules from the scenario rules array.
7. Commit ip rules in the harness (rules_committed becomes true).
8. Persist /app/state/netifd.snapshot.json (see /app/docs/staging-snapshot.md).

Apply must not write the staging snapshot before step 7 completes.

Apply never runs teardown automatically. A scenario field run_teardown true is metadata for harness tests only; teardown requires the separate teardown subcommand.

## Reload sequence

Reload must release all PD leases for the iface, clear routes, addresses, and rules without resetting PD lease history incorrectly, then run the apply core again without a full harness reset.

See /app/docs/pd-lease-contract.md for PD release requirements on reload.

## Teardown sequence

When the teardown subcommand is invoked:

1. Mark link down (down_ack false).
2. Acknowledge link down.
3. Remove the default route for the iface.
4. Run route rollback (see /app/docs/route-rollback-contract.md).
5. Rewrite /app/state/netifd.snapshot.json from the updated harness state so export reflects the post-teardown event log, routes, and route_binding.

Teardown must not delete the default route before step 2 completes.
