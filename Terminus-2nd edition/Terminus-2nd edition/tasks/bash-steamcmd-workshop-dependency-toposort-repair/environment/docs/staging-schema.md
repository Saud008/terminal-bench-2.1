# Parsed manifest staging schema

Stage 1 persists VDF parse output before dependency resolution.

## Paths

| Path | Writer | Reader |
|------|--------|--------|
| `/app/state/parsed-manifest.tsv` | `/app/lib/staging.sh` | `/app/lib/deps.sh`, `/app/lib/topo.sh` |
| `/app/state/staging-meta.json` | `/app/lib/staging.sh` | `/app/lib/export_plan.sh` |

## `parsed-manifest.tsv`

Tab-separated rows emitted by `/app/lib/vdf_parse.sh`:

- `MOD\t{mod_id}\t{version}`
- `DEP\t{from_mod}\t{to_mod}\t{constraint}\t{optional}`

Rows preserve manifest declaration order. The staging file must be a byte-for-byte copy of the parse stream for the current manifest.

## `staging-meta.json`

```json
{
  "staging_version": 1,
  "parsed_sha256": "<sha256 hex of parsed-manifest.tsv>",
  "line_count": 12
}
```

`export_plan.sh` must recompute the digest from `parsed-manifest.tsv` and reject export when it does not match `parsed_sha256`.
