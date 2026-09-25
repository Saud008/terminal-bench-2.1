# Policy snapshot and audit witness contract

Tamper-evident policy trust metadata staged before access-request evaluation.

Before evaluating requests, `casctl enforce` writes `/app/state/casctl/policy-snapshot.json` describing the loaded policy engine for the configured seed.

## Snapshot fields

```json
{
  "seed": "casbin-seed-1",
  "bundles": ["bundle-b", "bundle-a", "bundle-c"],
  "policy_fingerprint": "<sha256-hex>",
  "grouping_fingerprint": "<sha256-hex>"
}
```

- `bundles` lists bundle directories actually loaded for the seed (subset and shuffled merge order of config candidates).
- `policy_fingerprint` is the lowercase SHA-256 hex digest of UTF-8 bytes formed from canonical sorted policy tuples `priority|sub|dom|obj|act|eft` joined by `\n`, with a trailing `\n` after the last tuple (an empty engine hashes the single byte `\n`).
- `grouping_fingerprint` is the lowercase SHA-256 hex digest of UTF-8 bytes formed from canonical sorted grouping tuples `child|parent|dom` joined by `\n`, with a trailing `\n` after the last tuple.

Policy sorting for fingerprinting uses ascending `priority`, then `sub`, then `dom`, then `obj`, then `act`. Grouping sorting uses ascending `child`, then `parent`, then `dom`.

## Audit digest canonical form

The enforcement report `audit_digest` field is the lowercase SHA-256 hex digest of UTF-8 bytes built as follows:

1. Read `policy_fingerprint` and `grouping_fingerprint` from the staged snapshot at `/app/state/casctl/policy-snapshot.json` (same values written before request evaluation).
2. Build a list of lines in this exact order:
   - Line 1: `policy_fingerprint`
   - Line 2: `grouping_fingerprint`
   - Line 3: loaded bundle names from the snapshot `bundles` array, comma-separated with no spaces (e.g. `bundle-b,bundle-a,bundle-c`)
   - One line per export `results` row in request input order: `{sub}|{dom}|{obj}|{act}|{decision}|{match_count}` where `match_count` is a decimal integer with no leading sign
   - Final line from export `stats`: `{requests}|{allows}|{denies}|{policies_loaded}|{groupings_loaded}` (all decimal integers)
3. Join every line with a single `\n` (no trailing newline after the final stats line).
4. Hash the joined string with SHA-256 and emit lowercase hex.

Field definitions for `results` and `stats` are in `/app/docs/report-schema.md`.
