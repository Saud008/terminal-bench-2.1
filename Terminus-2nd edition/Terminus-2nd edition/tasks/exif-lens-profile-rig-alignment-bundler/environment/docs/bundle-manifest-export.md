# Bundle manifest export

Export writes /app/output/bundle-manifest.json:

- align_generation: from align-generation.json generation field
- staging_generation: from align staging snapshot
- entries: aligned capture rows sorted by normalized_ms then capture_id
- missing_frames: per-slot missing frame indices from align stage
- manifest_digest: sha256 of normalized manifest body

## manifest_digest

1. Copy manifest object excluding manifest_digest.
2. Normalize floats equal to integers to integers.
3. JSON marshal with sorted object keys and compact separators.
4. SHA256 UTF-8 bytes to lowercase hex.

## Export gates

Export fails when align_generation is zero.

Export recomputes captures_digest from staged captures and rejects when it differs from capture-staging.json captures_digest.
