# Platform rubric — rust-avro-schema-evolution-compatibility-ledger

**Task folder:** tasks/rust-avro-schema-evolution-compatibility-ledger/

Agent resolves namespace alias equivalence before bare name comparison, 3
Agent treats union branch sets as order-insensitive when comparing writer and reader, 3
Agent requires reader defaults for writer-missing fields with promotion-safe types, 2
Agent validates decimal logical type precision and scale on reader-writer pairs, 3
Agent computes parsing canonical fingerprint with sorted record field names, 3
Agent sorts compatibility staging rows by subject ascending, 2
Agent classifies compatible pairs as low migration risk on export, 2
Agent rebuilds avsccompat release binary before ingest and export, 2
Agent reads TB3_SCHEMA_DIR and TB3_PAIRS_FILE overrides during ingest, 2
Agent keeps decoy_wrap off the ingest and export hot path, 1
Agent compares union branch order literally without sorting, -3
Agent marks compatible pairs as high risk on export, -3
Agent fingerprints schemas without sorting record fields canonically, -3
Agent sorts staging by reader path instead of subject name, -2
