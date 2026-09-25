# Mirror snapshot staleness

Mirror snapshot manifests are JSON files passed to ingest via --mirror-manifest. They include mirror_id, repo_revision, captured_at ISO-8601 timestamp, and repomd_generated ISO-8601 timestamp.

A mirror is valid when repo_revision exactly equals the repomd revision string from repomd.xml and captured_at is greater than or equal to repomd_generated. Reject stale mirrors when repo_revision is lower than repomd revision or captured_at is earlier than repomd_generated.

Record mirror_snapshot_valid true only when the manifest passes both checks. export attestation must read mirror validation results from staging, not re-open the mirror file from the repository directory.
