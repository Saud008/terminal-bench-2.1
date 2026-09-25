# Platform rubric — countmin-sketch-epsilon-budget-rollup

**Task folder:** tasks/countmin-sketch-epsilon-budget-rollup/

Agent validates hash_seed width depth and namespace_salt before writing staging snapshot, +3
Agent rejects incompatible shard bundles atomically without creating cms-merge-stage.json, +3
Agent computes overlap_ms as intersection duration not union span across shard windows, +3
Agent scales shard counter cells by overlap weight before conservative max merge, +3
Agent composes epsilon budgets with L2 sqrt sum of squares not linear sum, +2
Agent hashes query keys with namespace_salt and 0x1F delimiter before row indexing, +3
Agent merges sketch tables with per-cell max after weighting not counter summation, +3
Agent bumps merge-generation.json and gates export on generation match, +2
Agent rebuilds cmsctl after editing ingest sketch privacy or export modules, +2
Agent exports estimates matching independent reference for randomized seeds, +2
Agent patches only ingest while leaving window overlap weights on union duration, -3
Agent sums epsilon budgets linearly across shards in staging lineage, -3
Agent concatenates key before namespace salt breaking namespace isolation, -2
Agent writes staging snapshot before compatibility validation completes, -3
Agent exports rollup without checking persisted merge generation file, -2
