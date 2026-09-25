# Export manifest contract

The final audit report uses pipeline_version 1 (not version).

Required fields: pipeline_version, seed, rootfs, mount_steps (verbatim copy of snapshot mount_steps), hooks (array of {name, exit}), resolv_target, sources_digest, ok.

Each mount_steps record uses the snapshot schema from mount-dag.md: id, source, target, fstype, kind, options only. Do not add after or other mounts.json-only fields.

ok is true only when hooks_ok from staging is true AND gate_digest matches recomputation AND mount order is valid.

Never set ok true when any hook exit is non-zero.
