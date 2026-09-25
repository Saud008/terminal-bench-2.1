# Platform rubric — bleve-index-batch-segment-rollback-barrier-repair

**Task folder:** tasks/bleve-index-batch-segment-rollback-barrier-repair/

Agent verifies segment checksums with FNV-1 (multiply then xor) before committing segment files, +3
Agent rejects FNV-1a / decoy zap_wrap hash as the admission checksum, +2
Agent rolls back segment files and root-map pointers on checksum failure, +3
Agent clears on-disk open-batch.flag before calling merge scheduler, +3
Agent schedules merge-plan.json only when at least two segments are committed and the flag is absent, +3
Agent writes merge-plan segments[] matching the root map, +2
Agent leaves merge-plan absent after a single successful ingest, +2
Agent commits doc id counter only after checksum passes, +2
Agent sorts export ordered_keys using collator rank with unlisted keys after listed ranks, +3
Agent writes batch-snapshot.json with committed or rolled_back status, +2
Agent exports manifest only when every root-map segment file exists on disk, +2
Agent rebuilds blevectl with cargo before verifier pytest runs, +1
Agent patches decoy zap_wrap module alone leaving ingest export broken, -3
Agent uses FNV-1a xor-then-multiply for segment admission checksums, -3
Agent collapses unlisted collator keys onto rank 0, -3
Agent schedules merge while open_batch barrier still true, -3
Agent writes merge-plan after first segment commit, -3
Agent advances next_doc_id before checksum validation succeeds, -2
Agent sorts export keys by raw UTF-8 byte order ignoring collator config, -2
