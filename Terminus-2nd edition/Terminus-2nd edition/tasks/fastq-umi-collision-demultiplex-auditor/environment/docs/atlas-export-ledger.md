# Atlas export ledger

lumidmx atlas export reads /app/state/lane-read-staging.json and /app/state/umi-demux-ledger.json only.

It writes /app/output/umi-collision-atlas.json with atlas_version 1, ingest_seq, demux_seq, clusters copied from the ledger, and contamination_flags computed at export time.

Contamination flags list cross_sample rows when the same canonical_umi appears under more than one sample_id anywhere in ledger entries. Demux run must not write contamination flags.

/app/output/atlas-digest.txt is the lowercase hex SHA-256 of the compact JSON serialization of the atlas file using default serde field order without pretty printing.
