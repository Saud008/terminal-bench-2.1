# Platform rubric — tuf-delegation-threshold-rotation-verifier

**Task folder:** tasks/tuf-delegation-threshold-rotation-verifier/

Agent enforces recursive canonical JSON signing bytes for HMAC authenticity verification, +3
Agent enforces strict key expiry epoch less-than rule when counting quorum, +3
Agent deduplicates threshold signature keyids and excludes root-role reuse on targets, +3
Agent links snapshot targets_version to targets signed version exactly, +2
Agent resolves delegated path-scope admission by literal pattern score with lexicographic tie break, +3
Agent seals delegation decisions sorted by path with canonical audit digest attestation, +2
Agent rebuilds tufctl after editing /app/src so /app/bin/tufctl reflects the corrected logic, +2
Agent reads staging snapshot only for export without unrelated module edits, +1
Agent writes rejected-target evidence as JSONL for disallowed paths only, +2
Agent honors TB3_EPOCH_BIAS when verifying hidden metadata rotations, +2
Agent stages monotonic ingest_seq across repeated admit calls, +1
Agent verifies all three metadata roles meet threshold before allowing targets, +2
Agent selects the staging-narrow delegation for staging/artifacts paths by literal-score tie-break, +2
Agent applies internal double-glob and release single-segment path rules correctly, +2
Agent fails rotation at epoch boundary when earliest root key expires, +2
Agent wires the _legacy rotation tie-break helper into the export path, -2
Agent uses serde default map order for canonical bytes instead of sorted keys, -3
Agent counts duplicate signature rows twice toward threshold quorum, -3
Agent treats expired keys as valid when epoch equals expires_epoch, -3
Agent compares snapshot metadata version instead of targets_version linkage, -3
Agent picks delegation by raw pattern length ignoring literal character scoring, -2
