# Commit gate contract

After mount simulation, s2_write_mount_snapshot writes the snapshot file. s2_write_mount_gate reads that snapshot and writes /app/state/mount-gate/{rootfs}-{pid}.json.

Gate record schema version 1:

- snapshot_path: absolute path to the mount snapshot
- mount_fingerprint: sha256 of newline-joined mount ids in mount_steps order
- mount_count: length of mount_steps
- gate_digest: sha256 of canonical JSON {"mount_count", "mount_fingerprint", "snapshot_path"} with sorted keys

The gate must reject snapshots whose mount_steps violate mount-dag.md ordering.
