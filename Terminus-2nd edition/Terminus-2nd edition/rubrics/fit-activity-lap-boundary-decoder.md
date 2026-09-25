# Platform rubric — fit-activity-lap-boundary-decoder

**Task folder:** tasks/fit-activity-lap-boundary-decoder/

Agent validates FIT message-stream CRC on fitlap decode before lap parsing, +3
Agent writes lap staging JSON under /app/state/lap-staging before export JSON, +3
Agent applies decode-only lap and record alignment rejection without blocking export path, +3
Agent reads lap start_time as little-endian per fit-lap-contract.md, +2
Agent maps trigger_code byte to manual/time/distance/session-end labels per fit-lap-contract.md, +2
Agent reads inline 12-byte note slot UTF-8 per lap record, +2
Agent computes staging digest over start_time ordered lap rows for shuffle fixtures, +3
Agent exports JSON from on-disk staging snapshot not a second FIT parse, +3
Agent exposes LapStaging source and stem fields matching export_from_staging arguments, +2
Agent rejects laps where end_time is not strictly greater than start_time, +2
Agent keeps decoy/legacy_merge.rs off the export hot path, +1
Agent patches only CRC while leaving incorrect lap boundary ranges in staging, -3
Agent fixes export JSON but skips staging file persistence on hard fixtures, -3
Agent applies decode alignment rejection during fitlap laps export, -2
Agent sorts export lap rows by message order instead of start_time, -2
Agent binds developer notes by sorted row position not original lap index, -2
