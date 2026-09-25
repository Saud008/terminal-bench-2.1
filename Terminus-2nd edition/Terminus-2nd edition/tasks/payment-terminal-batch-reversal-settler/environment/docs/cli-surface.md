# termsetctl CLI surface

Binary path: /app/bin/termsetctl

## compile-journal

Loads a scenario transcript bundle, normalizes transaction state, pairs reversals, applies cutoff filtering and sequence guards, and writes /app/state/batch-journal.jsonl plus journal metadata at /app/state/journal-meta.json.

Flags:
- --scenario SCENARIO (required)
- --fixture-dir PATH (default /app/fixtures)

## seal-bundle

Reads the compiled journal, builds /app/output/settlement-bundle.json, and writes /app/output/settlement-witness.hmac using the terminal batch key from the scenario fixture.

Flags:
- --scenario SCENARIO (required)
- --fixture-dir PATH (default /app/fixtures)

Rebuild after source edits: /app/scripts/verifier-rebuild.sh
