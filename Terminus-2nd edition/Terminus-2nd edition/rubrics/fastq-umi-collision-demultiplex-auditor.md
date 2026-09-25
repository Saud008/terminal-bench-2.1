# Platform rubric — fastq-umi-collision-demultiplex-auditor

**Task folder:** tasks/fastq-umi-collision-demultiplex-auditor/

Agent applies lane_first overrides before global manifest barcodes per lane, +3
Agent requires both R1 and R2 mates with non-empty UMIs before demux assignment, +3
Agent ignores N positions when computing barcode Hamming mismatch budget, +2
Agent reverse-complements R2 UMIs before rotate-left seed shift canonicalization, +3
Agent sets collision cluster_id to lexicographically minimum canonical_umi in cluster, +3
Agent emits export-only cross_sample contamination flags from ledger canonical UMIs, +2
Agent rebuilds lumidmx after editing demux collision or export crates, +2
Agent reads lane-read staging and demux ledger during atlas export not raw FASTQ, +2
Agent edits decoy merge helpers expecting atlas export fix, -3
Agent resolves global manifest barcodes before lane overrides when lane_first, -3
Agent demultiplexes pairs with only one synced mate present, -2
Agent uses first pair_id string as collision cluster_id instead of canonical UMI, -2
Agent omits cross_sample contamination markers from atlas export, -3
