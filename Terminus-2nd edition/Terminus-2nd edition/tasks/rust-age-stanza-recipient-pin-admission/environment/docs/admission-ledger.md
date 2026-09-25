# Admission ledger and witness

## Witness — `/app/state/age-header-witness.json`

```json
{
  "files": [
    {
      "file_id": "alpha",
      "rel_path": "alpha.age",
      "parse_ok": true,
      "stanzas": [
        {"type": "X25519", "args": ["..."], "fingerprint": "..."}
      ]
    }
  ]
}
```

- `files` sorted ascending by `file_id`
- `type` preserves wire casing from the header
- `fingerprint` follows `/app/docs/recipient-fingerprint.md`

## Ledger — `/app/output/age-admission-ledger.json`

```json
{
  "decisions": [
    {
      "file_id": "alpha",
      "verdict": "admit",
      "reasons": [],
      "matched_pins": ["..."],
      "stanza_count": 1
    }
  ],
  "totals": {
    "admitted": 1,
    "denied": 0,
    "malformed": 0
  }
}
```

### Field rules

- `decisions` sorted ascending by `file_id`
- `reasons` sorted ascending lexicographically; empty on admit
- `matched_pins` = distinct fingerprints present in both the file’s stanzas and the policy pin set, sorted ascending
- `verdict` is exactly `admit` or `deny`
- `totals.malformed` counts decisions whose reasons include `malformed_header`
- `totals.denied` counts all deny verdicts (including malformed)
- `totals.admitted` counts admit verdicts
- Idempotent: re-running seal with the same witness must rewrite byte-identical ledger JSON (compact separators, UTF-8, trailing newline)

## Commands

```
agerecv stage-witness --corpus <dir> --policy <pins.json> --witness /app/state/age-header-witness.json
agerecv seal-ledger --witness /app/state/age-header-witness.json --policy <pins.json> --out /app/output/age-admission-ledger.json
```

`AGE_CORPUS_DIR`, when set, overrides `--corpus` for `stage-witness`.
