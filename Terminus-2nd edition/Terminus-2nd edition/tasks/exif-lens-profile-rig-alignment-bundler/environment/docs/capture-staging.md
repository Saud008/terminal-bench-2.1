# Capture staging

Ingest writes /app/state/capture-staging.json with:

- captures: array of EXIF capture rows from JSONL input
- captures_digest: sha256 hex digest of canonical capture lines
- mount_sha256: sha256 hex digest of mount inventory file bytes
- mount_path: absolute path to ingested mount inventory
- staging_generation: monotonic counter mirrored in staging-seq.json

## captures_digest algorithm

1. Sort captures by normalized_ms ascending (computed per exif-timestamp-normalization.md), then capture_id ascending.
2. For each capture object, marshal compact JSON and append a single newline.
3. SHA256 the UTF-8 body as lowercase hex (64 characters).

## staging-seq.json

```json
{"staging_generation": N}
```

Each ingest increments staging_generation by one.
