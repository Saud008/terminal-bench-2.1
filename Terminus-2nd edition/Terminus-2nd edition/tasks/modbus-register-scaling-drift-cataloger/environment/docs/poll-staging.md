# Poll staging

ingest writes /app/state/poll-staging.json to disk

## Fields

| Field | Semantics |
|-------|-----------|
| frames | Array of frame objects from ingest JSONL in file order |
| frames_digest | Lowercase hex sha256 of UTF-8 body built from canonical compact JSON lines sorted by received_ms then frame_id, one line per frame, newline between lines, trailing newline after last line |
| manifest_sha256 | Lowercase hex sha256 of raw manifest file bytes |
| manifest_path | Absolute path to the manifest JSON used during ingest |
| staging_generation | Integer copied from staging-seq after ingest bump |

## Staging sequence

/app/state/staging-seq.json holds staging_generation incremented on each successful ingest.

catalog and export read staging_generation from poll-staging.json and compare against catalog-generation.json.
