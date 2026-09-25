# Engineering problem contract

Fleet ZFS operators must decide which snapshots are safe to destroy during a reclaim rollout without running `zfs destroy` speculatively against production pools. A trustworthy preview has to union every hold, clone, and bookmark reference against the candidate snapshot list, then reconcile that against how much free space the pool actually has before a rollout is allowed to proceed at all.

Root cause gaps appear when hold checks, clone lineage checks, and bookmark checks are evaluated independently of each other instead of as a single per-snapshot gate chain, when the pool free-space floor is treated as a soft warning instead of a hard stop, and when reclaim ordering is not deterministic across repeated compiles of the same inventory.

The agent builds the zfshold load, compile, and publish stages on the working baseline under /app. Contracts in sibling docs define the inventory object schema, each gate's blocking condition, the deterministic reclaim ranking, and the ledger and atlas JSON shapes that downstream fleet tooling depends on.
