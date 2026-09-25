# Platform rubric — bash-awk-jsonl-windowed-aggregate-pipeline

**Task folder:** tasks/bash-awk-jsonl-windowed-aggregate-pipeline/
**Written:** 2026-07-28T00:15:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent implements first-win event_id dedup in ingest.awk before staging write, +3
Agent skips invalid numeric values in ingest without coercing to zero, +3
Agent uses UTC mktime and TZ=UTC wrapper for tumbling window buckets, +3
Agent writes bucket-rollup.ndjson with separate tenant and metric keys, +3
Agent validates ledger-manifest sha256 against accepted.ndjson before export, +3
Agent sets footer total_events from ingest stats not window bucket count, +2
Agent maintains run-seq.json with content fingerprint across reruns, +2
Agent sorts export windows and per-window series per contract order, +2
Agent honors documented gawk -v names for wrapper-to-stage path wiring, +2
Agent ignores window_legacy and merge decoy modules off agg-run hot path, +1
Agent patches only export.awk while leaving ingest dedup broken, -3
Agent fixes bucket alignment but skips manifest binding on export, -3
Agent sets TZ=UTC in wrapper without repairing ingest epoch parsing, -2
Agent concatenates tenant and metric without separator in bucket stage, -2
Agent counts window buckets in footer total_events field, -2
Agent fingerprints stream paths only ignoring same-path content changes, -2
