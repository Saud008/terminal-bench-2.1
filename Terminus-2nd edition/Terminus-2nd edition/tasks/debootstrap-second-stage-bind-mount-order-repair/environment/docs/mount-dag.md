# Mount DAG contract

Each rootfs fixture provides mounts.json with a mounts array. Every entry has id, source, target, fstype, options, kind (virtual or bind), and after (list of mount ids that must complete first).

Topological ordering rules (all must hold in the emitted mount_steps sequence):

1. Honor every after edge: if mount B lists A in after, A appears before B.
2. Parent path before child: when target /a is a prefix path of target /a/b, the parent mount must appear before the child mount.
3. proc and sysfs must appear before any kind=bind mount.
4. The dev bind mount (id devbind) must appear only after proc is mounted.
5. devpts must appear after devbind when its target path is nested under /dev.
6. Tie-break equal-rank mounts by ascending id.

Mount snapshots written to /app/state/mount-snapshots/ use schema version 1 with fields version, seed, rootfs, mount_steps.

Each mount_steps entry is an ordered record copied from mounts.json mount metadata without dependency edges. Required fields only:

- id: mount id string
- source: bind source or virtual filesystem name
- target: absolute mount path under the chroot tree
- fstype: filesystem type string
- kind: virtual or bind
- options: array of mount option strings (empty array when mounts.json omits options)

The after field from mounts.json must not appear in mount_steps. Ordering constraints from after are reflected only in record sequence, not as a per-step field.

The export manifest copies mount_steps verbatim from the snapshot per export-manifest.md.
