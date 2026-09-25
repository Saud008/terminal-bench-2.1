# Merge cache and replay session

## Merge cache

After every successful `hostsctl merge`, write `/app/work/merged/<bundle-name>.json`:

```json
{
  "fingerprint": "<sha256 hex>",
  "publish_seal": "<sha256 hex>",
  "merged": { "...": "same object as merge export" }
}
```

See `/app/docs/publish-staging.md` for staging path, publish seal computation, and publish validation.

Compute `fingerprint` as SHA-256 over UTF-8 bytes built in this order (fragments before manifest — do not reverse this order):

1. For each path in `allow_files` then `deny_files` (manifest list order): the relative path string, a newline (`\n`), the raw fragment file bytes, then another newline (`\n`).
2. Append the raw bytes of `manifest.json` (no path prefix, no leading path string).

Any fragment or manifest edit must change the fingerprint.

`hostsctl decide` must load rules from the cached `merged` object when the cache file exists **and** its `fingerprint` matches the current bundle **and** its `publish_seal` matches a fresh seal from `merged` (see `/app/docs/publish-staging.md`). If the cache is missing or stale, rebuild merged rules from disk, refresh staging and cache, then evaluate.

## Replay session

`hostsctl replay` reads a JSON session file (array of objects with `daemon`, `ip`, `decision`, `matched_rule_index`). For each entry it runs a fresh `decide` against the bundle (respecting cache rules above) and records mismatches. Export schema:

```json
{
  "bundle": "office-edge",
  "checked": 3,
  "mismatches": []
}
```

Exit code `0` when `mismatches` is empty, `1` when any tuple differs.

The Bash wrapper must **return that status to the shell**. A common failure mode is running `json_write` after the Python comparison: writing the export file succeeds and overwrites `$?`, so `replay_session` returns `0` even when the checker exited `1`. Capture the checker status immediately (`payload="$(python3 ...)"; rc=$?`), write the export, then `return "$rc"` (or `exit "$rc"` from `hostsctl replay`).
