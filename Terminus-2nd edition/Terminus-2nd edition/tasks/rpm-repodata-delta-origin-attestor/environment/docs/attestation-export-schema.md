# Attestation export schema

Path: /app/output/repo-attestation.json

Top-level fields:

- repo_id: basename of the ingested repository directory
- ingest_seq: integer copied from staging
- repomd_revision: string from staging
- checksum_ok: boolean from staging
- mirror_snapshot_valid: boolean from staging
- packages: array sorted by nevra ascending; each row has name, epoch, version, release, arch, nevra, lineage_rank
- module_defaults: array sorted by module ascending; each row has module, default_stream, default_profile
- origin_digest: string sha256: followed by 64 lowercase hex chars

origin_digest is SHA-256 over UTF-8 bytes of compact JSON with sorted keys for this object shape:

{"module_defaults":[...],"mirror_repo_revision":"...","packages":[nevra strings sorted],"repomd_revision":"..."}

Use only nevra strings in the packages list inside the digest payload, sorted lexicographically. mirror_repo_revision is the repo_revision string from the mirror manifest stored in staging.

The export command must write pretty-printed JSON with sort_keys true and a trailing newline.
