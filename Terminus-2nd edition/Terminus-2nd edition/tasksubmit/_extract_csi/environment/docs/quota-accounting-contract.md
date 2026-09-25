# Namespace quota accounting

Fleet namespace snapshot quotas cap projected restore bytes after rollout.

Projected bytes for a namespace is the sum of restore_size_bytes for all VolumeSnapshots in that namespace.

quota_violations lists namespaces where projected_bytes exceeds quotas max_snapshot_bytes. Each violation object includes namespace, projected_bytes, and max_snapshot_bytes.

Empty quota_violations emits JSON `[]`, never null.

Violations sort by namespace ascending.
