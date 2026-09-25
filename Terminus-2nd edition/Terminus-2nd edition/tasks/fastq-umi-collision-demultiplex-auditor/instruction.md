Implement the lumidmx FASTQ UMI collision demultiplex auditor on the working Rust baseline under /app. The tool ingests paired FASTQ reads from lane directories, writes a normalized lane-read staging snapshot at /app/state/lane-read-staging.json, runs UMI demultiplex and duplicate-family clustering into /app/state/umi-demux-ledger.json, and exports a collision atlas to /app/output/umi-collision-atlas.json with companion digest at /app/output/atlas-digest.txt

Your work must satisfy every contract cited below. The src/decoy module is not on the stage ingest, demux run, or atlas export hot path and must not be edited for a correct export.

Build /app/bin/lumidmx from the workspace root. Subcommands:

  lumidmx stage ingest --reads-dir DIR --manifest PATH --lanes PATH
  lumidmx demux run
  lumidmx atlas export

After stage ingest, /app/state/lane-read-staging.json must record precedence_order, mismatch_budget, umi_length, barcode_length, global samples, lane configs, and synced pair rows extracted from FASTQ mates.

demux run assigns sample_id per pair using effective lane barcodes, canonicalizes UMIs per mate, and builds collision clusters. cluster_id for each cluster is the lexicographically minimum canonical_umi among its pair_ids.

Paired ingest must follow /app/docs/paired-read-sync.md: both R1 and R2 mates are required with non-empty UMIs before a pair enters staging or the ledger.

Barcode assignment must follow /app/docs/barcode-mismatch-budget.md: Hamming distance ignores N positions and respects mismatch_budget.

UMI fields must follow /app/docs/umi-canonicalization.md: R1 rotate-left by lane seed_shift plus TB3_UMI_SEED_SHIFT, R2 reverse complement then rotate-left by the same shift, pair canonical_umi is lex min of mate canonical strings.

Lane barcodes must follow /app/docs/lane-manifest-precedence.md: when precedence_order is lane_first, lane overrides replace global manifest barcodes for the same sample_id within that lane.

atlas export follows /app/docs/atlas-export-ledger.md: contamination_flags are export-only cross_sample markers when one canonical_umi maps to multiple sample_ids in ledger entries.

Bundled fixtures live under /app/data/reads with companion files /app/data/manifest.json and /app/data/lanes.json. Hidden verifier fixtures may supply additional lanes, manifests, reads, and TB3_UMI_SEED_SHIFT at runtime.
