# Staging contract

s2_write_staging_manifest combines the mount snapshot path, gate path, hook summary, resolv_target, and sources_digest.

Staging schema version 1 fields:

- snapshot_path, gate_path, gate_digest
- seed, rootfs from meta
- mount_count, mount_fingerprint
- hooks_ok: true only when every hook exit is zero
- resolv_target, sources_digest
- stage_binding: sha256 of canonical JSON {mount_fingerprint, rootfs, seed, sources_digest} sorted keys

Ledger at /app/state/stage2-ledger.json appends one entry per successful run. Top-level schema:

- entries: array of ledger entry objects

Each ledger entry (version implicit, no wrapper field) contains:

- sequence: 1-based run counter within the ledger file
- seed: from staging manifest seed
- rootfs: catalog rootfs name from staging manifest rootfs (matches meta name)
- staging_path: absolute path to the staging manifest JSON written for this run
- stage_binding: sha256 binding copied from staging manifest stage_binding
