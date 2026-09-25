# Staging format

Staging manifests live at /app/stage/license-compliance/WORKSPACE_BASENAME.json.

Required fields after ingest: workspace_id, workspace_root, workspace_fingerprint, packages, duplicate_package_names, patch_map, ingest_complete.

workspace_fingerprint is sha256 over bytes of Cargo.lock, Cargo.toml, lock-metadata.json, and every file under vendor/ sorted by path.

After audit: findings (sorted by kind, package, version), audit_complete, audit_digest where audit_digest is sha256 of compact JSON encoding of findings with sort_keys true.

Run sequence is tracked in /app/state/run-seq.json and increments when workspace_fingerprint changes.
