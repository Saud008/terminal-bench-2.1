# Import-preview ledger

During `bundlectl verify`, import-preview runs before digest or scoped-signature math. The preview snapshot is persisted at `/app/state/preview-ledger.json`.

## Schema

```json
{
  "bundle": "<absolute bundle directory>",
  "order": ["data/data.json", "policies/allow.rego"],
  "entries": [
    {"raw": "./data/../data/data.json", "canonical": "data/data.json"}
  ]
}
```

## Ordering rules

- `entries` lists every manifest member except `MANIFEST.json` and `.signatures.json`, each with raw manifest path and POSIX-canonical preview path.
- `order` holds the same canonical paths sorted by **UTF-8 lexicographic order**. Manifest declaration order must not appear in `order`.
- Digest chain computation must iterate members in `order`, not manifest `members` array order.

## Relationship to digest chain

Rolling SHA-256 chain roots (full bundle and scoped subsets) use canonical paths from the preview ledger ordering. Scoped signature checks filter members by scope prefix, then apply the same rolling digest over the filtered subset sorted lexicographically.

The legacy helper in `/app/internal/verify/legacy_manifest_chain.go` computes roots using manifest declaration order for diagnostics only. Contract acceptance never uses manifest order.
