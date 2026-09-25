# Merge contract

`hostsctl merge` reads a bundle directory containing `manifest.json`, allow fragments, optional deny fragments, and optional daemon alias data.

## Manifest

```json
{
  "name": "office-edge",
  "allow_files": ["allow/10-base.allow", "allow/20-vpn.allow"],
  "deny_files": ["deny/10-block.deny"]
}
```

Paths are relative to the bundle root. Files are read in the order listed in each array.

Optional `daemon_aliases` may point at an alias file relative to the bundle root.

## Export

The merge export names the bundle, lists merged rules, and reports side counts in `stats`. Field definitions and examples are in `/app/docs/export-schema.md`.

Each rule object includes:

| Field | Meaning |
|-------|---------|
| `index` | Zero-based position in the merged `rules` array |
| `side` | `"allow"` or `"deny"` |
| `origin` | Source fragment path |
| `line` | 1-based line number in that fragment |
| `daemons` | Daemon names after alias normalization |
| `clients` | Client pattern strings from the fragment |

`stats.allow_rules` and `stats.deny_rules` count rules by side. `stats.total_rules` is their sum.

Merge output must depend only on manifest bytes and fragment contents, not on export path names. The merge-cache `fingerprint` algorithm is defined in `/app/docs/session-cache.md`.

Every rule with `side` `"allow"` must appear before any rule with `side` `"deny"` in the merged `rules` array. Reassign `index` sequentially across that combined list starting at zero.
