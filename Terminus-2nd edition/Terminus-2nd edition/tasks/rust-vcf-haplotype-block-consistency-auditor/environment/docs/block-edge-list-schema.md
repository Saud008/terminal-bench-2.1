# Block edge list schema

vcfaud wire-blocks writes /app/work/block-edge-list/<run-id>.jsonl as newline-delimited JSON.

The first line is a meta record with record_type meta, run_id, and merge_generation. merge_generation starts at one on first wire and increments on each rewire for the same run id.

Each subsequent edge line has record_type edge, block_id, chrom, ps_tag, sample_id, and variant_count for that block. Anomaly lines use record_type anomaly with anomaly_id, chrom, ps_tag, anomaly_type, sample_ids, and variant_positions. anomaly_id values follow the miss-/mix-/disc- templates in consistency-report-fields.md.

Each block_id groups edges sharing the same chrom and ps_tag. sample_ids on edges for a block sort ascending when aggregated.
