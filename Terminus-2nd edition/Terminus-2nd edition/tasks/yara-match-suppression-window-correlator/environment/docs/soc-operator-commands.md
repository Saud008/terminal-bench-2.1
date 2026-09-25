# yaracor SOC operator commands

Binary path: /usr/local/bin/yaracor

## Subcommands

### ingest

```
yaracor ingest --policy PATH --events PATH
```

Loads SOC policy manifest and YARA match events. Writes /app/state/event-staging.json and bumps /app/state/staging-seq.json with witness digests.

### correlate

```
yaracor correlate
```

Reads staged events and resolves policy from staging: prefer `policy_path` when present on disk, otherwise match `policy_sha256` under /app/fixtures or YARACOR_FIXTURE_DIR (see event-staging.md).
Applies trust policy gates per trust-policy-workflow.md.
Writes /app/state/correlate-generation.json and /app/output/rejected-events.jsonl

### export

```
yaracor export
```

Writes sealed /app/output/incident-bundle.json; refuses when correlate_generation is zero.
Validates events_digest witness in staging before sealing bundle_digest.

### run

```
yaracor run --policy PATH --events PATH
```

Executes ingest, correlate, and export in order.

## Environment

YARACOR_FIXTURE_DIR overrides the fixture root for hidden verifier policy resolution when `policy_path` is unavailable.
