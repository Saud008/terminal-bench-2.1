# Snapshot guard (stage 1b)

After stage 1 writes the bind snapshot and before stage 2a opens it, `snapshot_guard.rs` validates bind invariants that are not re-checked during export.

Stage 1b runs inside `nlctl decode` immediately after stage 1 writes the bind snapshot file. The guard reads the on-disk snapshot JSON and validates invariants before stage 2a opens it. Failures return a non-zero exit and must not create an NH snapshot or export file.

Multipath routes must not attach route-level `RTA_METRICS` values onto individual nexthop rows. Single-path routes may carry metrics on their lone nexthop per `/app/docs/nldm-dump-wire.md`.

See `/app/docs/bind-stage-artifact.md` for stage ordering.
