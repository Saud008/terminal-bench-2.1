# Event staging

Ingest writes /app/state/event-staging.json with:

- events: array of scan event objects from the JSONL input
- events_digest: sha256 hex digest of canonical event lines
- policy_sha256: sha256 hex digest of the policy file bytes
- policy_path: absolute path of the policy file passed to ingest
- staging_generation: monotonic counter mirrored in staging-seq.json

## Policy resolution for correlate

Correlate loads the SOC policy from staging as follows:

1. If `policy_path` is non-empty and the file exists, use that path.
2. Otherwise resolve by matching `policy_sha256` against candidate files under the fixture root (`/app/fixtures`, or `YARACOR_FIXTURE_DIR` when set), trying `policy/policy-east.json` then `policy.json`.

Parametrized and off-catalog verifier runs ingest policies outside `/app/fixtures`; those paths rely on the `policy_path` witness. SHA-only lookup under the fixture root is not sufficient for those cases.

## events_digest algorithm

1. Sort events by `detected_ms` ascending, then `event_id` ascending.
2. For each event, marshal one compact JSON object (separators comma and colon, no spaces) using **this exact field order**, then append a single newline (`\n`):

   `event_id`, `asset_id`, `sample_sha256`, `rule_name`, `rule_revision`, `detected_ms`, `scanner_host`

   Field order is part of the digest contract. Emitting the same keys in any other order changes the hashed bytes. Omit no listed fields; do not insert extra keys into the digest line.
3. Concatenate those lines in the sorted event order (no trailing blank line beyond the final newline after the last event).
4. SHA256 the UTF-8 body and encode as lowercase hex (64 characters).

## staging-seq.json

```json
{"staging_generation": N}
```

Each ingest increments staging_generation by one.
