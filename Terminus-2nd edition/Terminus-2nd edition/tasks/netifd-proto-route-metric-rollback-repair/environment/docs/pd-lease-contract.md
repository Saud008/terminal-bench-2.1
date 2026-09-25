# PD lease contract

When pd_prefix is set on a scenario, apply acquires one PD lease record with pd_lease_id (default pd-default).

Reload must call pd_release for the iface before re-applying so at most one active lease exists per iface after reload completes.

Export pd_leases lists active leases after the last operation.
