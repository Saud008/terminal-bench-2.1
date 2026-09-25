# Conservative merge contract

Count-Min Sketch tables are depth-by-width matrices of unsigned 64-bit counters. Updates add an integer count to every row at the row index derived from the namespaced key.

Merging weighted shard tables uses conservative aggregation: merged[row][col] = max over shards s of floor(shard_s[row][col] * weight_s). Never sum counter cells across shards.

Point estimates for a query key return the minimum counter value across rows at that key indices, standard Count-Min query semantics.

The merge phase writes merged_counters into staging and bumps /app/state/merge-generation.json, then export requires merge_generation in staging to match the generation file and be greater than zero.
