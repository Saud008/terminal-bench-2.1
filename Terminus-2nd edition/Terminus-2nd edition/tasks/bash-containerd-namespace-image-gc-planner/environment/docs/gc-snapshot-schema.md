# gc_snapshot.json schema

Fields: schema_version, namespaces, images, leases, snapshots, meta_digest.

meta_digest changes bump /app/state/revision.seq on scan-meta when the digest differs from the previous gc snapshot file.
