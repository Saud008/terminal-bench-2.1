Implement the tantictl segment compaction governor on the working Rust baseline under /app. The tool ingests on-disk inverted index segment descriptors from a directory, writes a normalized staging snapshot at /app/state/tantivy-stage.json, runs the merge engine to compact delete bitsets and posting statistics, and exports live segment metrics to /app/output/segment-stats.json with companion digest at /app/output/merge-checksum.txt

Your work must satisfy every contract cited below. The src/decoy module is not on the ingest or merge export hot path and must not be edited for a correct export.

Build /app/bin/tantictl from the workspace root. Subcommands:

  tantictl ingest <segments-dir>
  tantictl merge export [--pass N]

After ingest, /app/state/tantivy-stage.json must list segments in source filename order with segment_id, max_doc, local delete_bits, and term posting rows copied from the JSON fixtures.

merge export reads staging only (never re-parse raw segment JSON from the ingest directory). It writes /app/output/segment-stats.json and derives /app/output/merge-checksum.txt from the canonical stats JSON defined in /app/docs/export-checksum.md

Delete bitset compaction must follow /app/docs/delete-bitset-remap.md: remap each segment local deleted doc id into the merged global doc id space before unioning bitsets. OR-ing local bit positions across segments without remap is incorrect.

Term frequency rollup must follow /app/docs/term-freq-after-deletes.md: merged term freq totals must subtract each posting row deleted_hits count before summing across segments. Summing raw freq without tombstone subtraction is incorrect.

Live max_doc export must follow /app/docs/live-max-doc-union.md: live_max_doc is the exclusive upper bound on allocated global doc ids after concatenating segment doc spaces, not the maximum single-segment max_doc field.

Field norm bytes on merged posting rows must follow /app/docs/field-norm-encoding.md: norm values export as unsigned 8-bit integers in the stats JSON manifest, not wider integer types.

Idempotent re-compaction must follow /app/docs/merge-idempotency.md: a second merge export pass with --pass 2 must produce the same delete bitset and checksum as pass 1 when staging is unchanged. Duplicate OR of delete bits from persisted merge state is incorrect.

Bundled fixtures use the /app/data/segments directory. Hidden verifier fixtures may supply additional segment directories and TB3_SEGMENT_SEED doc id permutation at runtime.
