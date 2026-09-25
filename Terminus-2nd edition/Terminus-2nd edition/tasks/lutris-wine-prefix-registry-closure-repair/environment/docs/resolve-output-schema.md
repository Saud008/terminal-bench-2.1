# Resolve output schema

Written to `--output` as UTF-8 JSON with `sort_keys=true` and a trailing newline.

```json
{
  "resolve_version": 1,
  "registry_dir": "<absolute path>",
  "root_slug": "<slug>",
  "runner": "<runner id or null>",
  "prefix": "<canonical absolute path or null>",
  "dxvk_version": "<version string or null>",
  "closure": ["<slug>", "..."],
  "warnings": ["<string>", "..."],
  "errors": ["<string>", "..."],
  "cycles": ["<slug,slug,...>", "..."],
  "stats": {
    "entry_count": 0,
    "edge_count": 0,
    "max_depth": 0
  }
}
```

- `closure` is dependency-first topological order including `root_slug` last.
- `cycles` lists each detected cycle as comma-joined slugs in discovery order (no spaces).
- `stats.max_depth` is the longest `requires` chain depth from root (root depth 0).
