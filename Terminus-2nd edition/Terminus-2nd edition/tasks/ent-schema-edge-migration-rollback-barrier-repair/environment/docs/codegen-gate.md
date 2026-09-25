# Codegen gate

Atlas snapshot steps must refuse stale ent codegen fingerprints. The literal hash ent-codegen-v2-stale is invalid.

Codegen refresh must hash codegen_seed and target_version together into an eight-byte hex prefix stored in migration-report.json as codegen_hash.

Snapshot_seq records table count at snapshot time and must be recorded only after codegen_refresh in the events list.
