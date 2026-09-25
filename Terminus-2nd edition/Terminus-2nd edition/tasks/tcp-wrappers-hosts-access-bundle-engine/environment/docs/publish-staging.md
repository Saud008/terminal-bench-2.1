# Publish staging

`merge` does not write the merge cache directly. It builds a merged payload, writes a **staging artifact**, then **publishes** into the fingerprinted cache.

## Staging path

After merge builds the merged object, write `/app/work/staging/<bundle-name>.json`:

```json
{
  "bundle": "office-edge",
  "merged": { "...": "same object as merge export" },
  "publish_seal": "<sha256 hex>"
}
```

The staging file must exist before the cache file is updated.

## Publish seal

Compute `publish_seal` as SHA-256 over UTF-8 bytes of this JSON object (compact: sorted keys, `,` separators, no spaces):

```json
{
  "allow_rules": <int>,
  "deny_rules": <int>,
  "total_rules": <int>,
  "first_deny_index": <int>,
  "sides": ["allow", "allow", "deny", ...]
}
```

- `first_deny_index` is the index of the first rule whose `side` is `"deny"`, or `total_rules` when there are no deny rules.
- `sides` lists each merged rule's `side` in final export order (allow rules before deny).

The seal binds stats **and** allow-before-deny ordering. A merged export with correct stats but deny-before-allow order must produce a different seal.

## Publish step

`publish_from_staging` reads the staging file, recomputes `publish_seal` from `merged`, and **must reject** when the stored seal differs. On success it writes `/app/work/merged/<bundle-name>.json`:

```json
{
  "fingerprint": "<fragment fingerprint>",
  "publish_seal": "<publish seal>",
  "merged": { "...": "same object as staging merged" }
}
```

Then write the merge `--export` JSON (the `merged` object only — no cache wrapper fields).

## Decide and cache

`load_cached_rules` accepts a cache only when **both** `fingerprint` matches the current bundle **and** `publish_seal` matches a fresh seal recomputation from `merged`. Missing or stale seals force a rebuild through the full merge → staging → publish path.
