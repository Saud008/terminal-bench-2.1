# Platform rubric — rust-zarr-array-coordinate-consolidator

**Task folder:** tasks/rust-zarr-array-coordinate-consolidator/

Agent rebuilds zarrmeta before invoking ingest and export, +3
Agent validates chunk grid slot counts with ceiling division per axis, +3
Agent fixes coordinate length matching against shape dimensions in axis order, +2
Agent computes missing chunk keys as expected minus present only, +3
Agent fingerprints compressors with id level and shuffle in seal payload, +2
Agent sorts staging snapshot rows by array_name ascending, +2
Agent exports totals missing_chunks as sum of missing key lengths, +3
Agent applies TB3_MANIFEST_DIR override for hidden humidity manifest, +2
Agent reads coordinate spans using offset plus scale times index, +2
Agent writes consolidated manifest arrays sorted by name, +1
Agent patches grid_slots without floor division on partial chunks, -3
Agent fixes only chunk_missing while leaving transform axis order reversed, -3
Agent hardcodes consolidated manifest JSON in tests or solution, -5
Agent edits telemetry_decoy expecting it to fix export totals, -2
Agent skips rebuild in test.sh before pytest subprocess checks, -3
