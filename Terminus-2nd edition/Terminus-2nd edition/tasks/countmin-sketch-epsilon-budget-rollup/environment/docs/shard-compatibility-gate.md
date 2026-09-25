# Shard compatibility gate

Every shard in a bundle must share identical hash_seed, width, depth, and namespace_salt fields. The ingest phase compares these fields before writing /app/state/cms-merge-stage.json,

When any shard disagrees on hash_seed, width, depth, or namespace_salt, cmsctl ingest must exit with a non-zero status and leave /app/state/cms-merge-stage.json unchanged, with no partial staging writes

Before comparing shards, adjust each file `hash_seed` by adding the FNV-1a 64-bit offset of the `--seed` string (full algorithm in /app/docs/merge-stage-schema.md). `/app/fixtures/seeds.json` lists allowed bundled seed names only — it does not define offset magnitudes. Width and depth come from the bundle manifest unchanged unless TB3_WIDTH_BIAS is set by the verifier harness.
