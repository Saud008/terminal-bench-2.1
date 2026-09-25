# Weight audit flow

Catalog scan walks manifest JSON files in lexicographic order, validates each tensor against safetensors shard bytes, and appends rows to /app/var/xr7_journal.ndjson. Each journal row receives a run_seq that increases monotonically across the entire catalog scan batch, not restarting per manifest_id.

Atlas publish reads the journal plus the same catalog and weight roots to emit /app/lineage/weight_lineage_atlas.json with deterministic violation sort sequence.
