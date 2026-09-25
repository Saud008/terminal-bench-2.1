# Shard compatibility gate

Every shard in a bundle must share identical hash_seed, width, depth, and namespace_salt fields. The ingest phase compares these fields before writing /app/state/cms-merge-stage.json,

When any shard disagrees on hash_seed, width, depth, or namespace_salt, cmsctl ingest must exit with a non-zero status and leave /app/state/cms-merge-stage.json unchanged, with no partial staging writes

Seed-derived offsets from /app/fixtures/seeds.json apply to hash_seed only during bundled fixture resolution; width and depth come from the bundle manifest unchanged unless TB3_WIDTH_BIAS is set by the verifier harness.
