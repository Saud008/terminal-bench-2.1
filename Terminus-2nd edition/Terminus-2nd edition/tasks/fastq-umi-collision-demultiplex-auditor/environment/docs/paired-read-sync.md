# Paired read sync

lumidmx stage ingest pairs FASTQ mates by pair_id stem before writing /app/state/lane-read-staging.json pairs

Each lane directory under the reads-dir contains files named pair_id_R1.fastq and pair_id_R2.fastq. A staged pair row requires both mates present with non-empty extracted UMIs.

demux run must consume only synced pairs from staging. Partial pairs ingested without a mate must never appear in /app/state/umi-demux-ledger.json entries.

The pair_id field is the filename stem shared by both mates in a lane.
