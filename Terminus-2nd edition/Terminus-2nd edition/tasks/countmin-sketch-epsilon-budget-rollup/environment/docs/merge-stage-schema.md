# Merge staging schema

`cmsctl ingest` writes `/app/state/cms-merge-stage.json` only after shard compatibility and non-zero window overlap checks succeed. `cmsctl merge` updates the same file with merged sketch counters and bumps `merge_generation`. Export and generation gating read this snapshot per `/app/docs/lineage-export-schema.md`.

## `/app/state/cms-merge-stage.json`

JSON object with these fields:

- `engine` — literal string `cms-hash-v2` identifying the row-index hash family used for sketch updates and queries.
- `bundle_id` — string bundle identifier from the manifest (matches `--bundle`).
- `hash_seed` — unsigned 64-bit integer shared by every shard after the `--seed` offset is applied (see seed offset below). This is the seed used for row indexing and export estimates.
- `width` — sketch table width in columns (unsigned integer). May include `TB3_WIDTH_BIAS` when set by the verifier harness.
- `depth` — sketch table depth in rows (unsigned integer).
- `namespace_salt` — string namespace prefix for salted key hashing per `/app/docs/salted-key-namespace.md`.
- `overlap_ms` — unsigned integer intersection duration in milliseconds across shard windows per `/app/docs/window-overlap-weighting.md`.
- `window_weights` — object mapping each `shard_id` to its overlap weight `overlap_ms / window_ms` as a floating-point number.
- `shard_fingerprints` — array of lowercase hex SHA-256 digests, one per shard in manifest ingest order. Each digest hashes, in order: `shard_id` UTF-8 bytes, `hash_seed` as little-endian u64, `width` as little-endian u64, `depth` as little-endian u64, `namespace_salt` UTF-8 bytes (all values after seed offset and width bias).
- `epsilon_lineage` — object with `raw_epsilons` (array of floats, one per shard in ingest order) and `composed_epsilon` (L2 composition per `/app/docs/epsilon-composition.md`).
- `merge_generation` — unsigned integer. `0` after ingest; incremented by each successful merge and mirrored in `/app/state/merge-generation.json`.
- `query_keys` — array of strings copied from the bundle manifest; export estimates every listed key.
- `merged_counters` — absent or JSON `null` after ingest. After merge, a `depth`-by-`width` matrix of unsigned integers: outer index is row, inner index is column, holding the conservatively merged table per `/app/docs/conservative-merge-contract.md`.

Ingest must not write this file when compatibility fails or `overlap_ms` is zero. Merge must populate `merged_counters` before export is allowed.

## Seed offset for `hash_seed`

The `--seed` flag names a run identifier (bundled names are listed in `/app/fixtures/seeds.json`). **`seeds.json` does not store offset values** — it only enumerates allowed seed names for bundled fixtures.

Before compatibility checks, derive a 64-bit offset from the seed string with FNV-1a over UTF-8 bytes:

```
offset = 0xcbf29ce484222325
for each byte b in seed UTF-8:
    offset = offset XOR b
    offset = (offset * 0x100000001b3) mod 2^64   // wrapping multiply
```

Apply the offset to every loaded shard file:

```
adjusted_hash_seed = (shard_file.hash_seed + offset) mod 2^64   // wrapping add
```

Compatibility checks, fingerprints, sketch tables, staging `hash_seed`, and export estimates all use `adjusted_hash_seed`. Width, depth, and `namespace_salt` are taken from shard files unchanged except for `TB3_WIDTH_BIAS` on width.
