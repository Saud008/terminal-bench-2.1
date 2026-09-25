# Platform rubric — exif-lens-profile-rig-alignment-bundler

**Task folder:** tasks/exif-lens-profile-rig-alignment-bundler/

Agent normalizes EXIF timestamps by subtracting timestamp_tz minutes from UTC-parsed base milliseconds, +3
Agent matches lens profile revisions using highest effective_capture_ms not exceeding normalized_ms, +3
Agent rejects captures whose lens_id is absent from the slot allowed_lens_ids inventory, +3
Agent rejects checkerboard rows where board_detected is false with calibration_failed reason, +3
Agent computes per-slot missing frame indices with inclusive frame_index_start and expected_frames_per_slot, +3
Agent writes capture-staging.json with sha256 captures_digest sorted by normalized time then capture_id, +3
Agent bumps align-generation.json only after align completes and blocks export when generation is zero, +2
Agent validates staging captures_digest during export before writing bundle-manifest.json, +3
Agent writes manifest_digest as sha256 of canonical bundle body without that field, +2
Agent leaves wrap decoy focal bump helpers off align and export hot path, +1
Agent patches export manifest only while captures_digest validation remains disabled, -3
Agent fixes rig slot checks but keeps wrong EXIF tz sign in normalize_exif_ms, -3
Agent edits wrap decoy expecting bundle entries to change without align module edits, -2
Agent selects first lens profile row instead of revision-effective profile for capture time, -2
Agent skips rebuild-rigbundle after editing lib shell modules before pytest, -2
