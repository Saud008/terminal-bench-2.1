# Finding staging

scan writes /app/state/finding-staging.json to disk.

## Fields

| Field | Semantics |
|-------|-----------|
| findings | Array of normalized finding objects from SARIF |
| findings_digest | Lowercase hex sha256 of the digest body below |
| sarif_sha256 | Lowercase hex sha256 of raw SARIF file bytes |
| policy_sha256 | Lowercase hex sha256 of raw policy file bytes |
| policy_path | Absolute path to the policy JSON used during scan |
| remap_path | Absolute path to the remap JSON used during scan |
| baseline_path | Absolute path to the baseline JSON used during scan |
| scan_revision | Integer copied from staging-seq after scan bump |

## Staging sequence

/app/state/staging-seq.json holds scan_revision incremented on each successful scan.

curate and emit read scan_revision from finding-staging.json and compare against reconcile-revision.json.

## findings_digest serialization

Build the digest body from the scan finding list before hashing:

1. Sort findings by observed_at ascending, then finding_id ascending (lexicographic).
2. For each sorted finding, emit one compact JSON object on its own line with no spaces after colons or commas.
3. Each line object must use exactly these keys in this order: finding_id, tool, rule_id, level, uri, start_line, start_column, fingerprint, observed_at.
4. Terminate every line with a single newline (U+000A), including after the last finding line.
5. UTF-8 encode the concatenated body and take lowercase hex sha256.

emit refuses when findings_digest on staging does not match a recomputation from findings.
