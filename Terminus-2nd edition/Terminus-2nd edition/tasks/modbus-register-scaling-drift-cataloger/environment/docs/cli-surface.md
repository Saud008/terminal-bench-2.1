# CLI surface

modbusctl lives at /usr/local/bin/modbusctl.

## Subcommands

| Subcommand | Purpose |
|------------|---------|
| ingest | Read manifest + frames JSONL, write poll staging snapshot |
| catalog | Decode staged frames, apply scaling and drift rules, bump catalog generation |
| export | Validate staging + catalog generation, write drift catalog and rejected frames |
| run | ingest then catalog then export in one invocation |

## ingest flags

--manifest path to device manifest JSON
--frames path to poll frames JSONL

Writes /app/state/poll-staging.json and updates /app/state/staging-seq.json on disk

## catalog flags

No required flags. Reads staging snapshot and manifest referenced by manifest_sha256 hash match.

Writes /app/state/catalog-generation.json on disk

## export flags

No required flags. Writes /app/output/drift-catalog.json and /app/output/rejected-frames.jsonl on disk

## run flags

Same as ingest plus executes catalog and export afterward.

## Environment

TB3_FIXTURE_DIR when set replaces /app/fixtures for manifest and frame resolution in verifier hidden scenarios.
