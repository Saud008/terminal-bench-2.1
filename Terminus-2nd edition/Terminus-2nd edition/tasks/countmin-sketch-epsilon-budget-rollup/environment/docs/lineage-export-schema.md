# Lineage export schema

Export writes JSON to the path passed to cmsctl export --output with these fields (staging field definitions in /app/docs/merge-stage-schema.md):

bundle_id: string copied from staging
merge_generation: integer loaded from /app/state/merge-generation.json,
overlap_ms: integer from staging
estimates: object mapping each bundle query key to unsigned integer estimate
epsilon_lineage: object with raw_epsilons array and composed_epsilon float
stage_digest: lowercase hex sha256 of canonical staging JSON with merged_counters and merge_generation fields removed, keys sorted, no whitespace

Export reads staging only; it must refuse when merge_generation is zero or mismatched with the generation file.
