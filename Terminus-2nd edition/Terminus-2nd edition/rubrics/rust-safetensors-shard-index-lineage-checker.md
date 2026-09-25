# Platform rubric — rust-safetensors-shard-index-lineage-checker

**Task folder:** tasks/rust-safetensors-shard-index-lineage-checker/

Agent validates tensor data_offsets against payload section length not whole file size, +3
Agent computes BF16 element byte width as two bytes per elem_layout_rules.md, +3
Agent fingerprints payload windows using payload-relative data_offsets (not file-absolute), +3
Agent normalizes LoRA lineage hashes with optional 0x/0X strip then ASCII case-insensitive compare, +3
Agent assigns globally monotonic run_seq across manifests and shards, +3
Agent emits LINEAGE_HASH plus per-row LINEAGE_ROW and sorts by tensor then code, +3
Agent writes journal rows to /app/var/xr7_journal.ndjson during catalog-scan, +2
Agent publishes /app/lineage/weight_lineage_atlas.json during atlas-publish, +2
Agent rebuilds xr7 release binary before subprocess verifier grading, +2
Agent honors XR7_CATALOG_ROOT and XR7_WEIGHT_ROOT probe overrides, +2
Agent validates dtype shape product against offset span from safetensors header, +2
Agent treats header-inclusive offset end as valid when payload slice is exceeded, -3
Agent uses four-byte BF16 sizing and misreports tensor payload spans, -3
Agent hashes file-absolute windows or whole-file bytes for shard fingerprint, -3
Agent accepts case fold alone but fails optional 0x prefix lineage normalization, -3
Agent restarts run_seq per shard or omits LINEAGE_ROW / sorts by code first, -3
