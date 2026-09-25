# Platform rubric — icc-softproof-gamut-drift-bundler

**Task folder:** tasks/icc-softproof-gamut-drift-bundler/

Agent writes icc.stage.json beside dirname(readings) not a global /app/state path, +3
Agent resolves duplicate patch_id lines by keeping the last file occurrence, +3
Agent computes CIE76 delta E with sqrt of summed squared LAB differences, +3
Agent walks paper batch parent links to inherit gamma_anchor for PB-CHILD batches, +3
Agent selects rendering intent by first policy intent_precedence hit in profile map, +3
Agent validates profile checksum from checksum_fields subset only not whole file bytes, +3
Agent treats calibration ticket valid_from_epoch boundary as inclusive at evaluate as_of, +3
Agent populates staging evaluation before export and refuses export without evaluation block, +2
Agent exports drift report from frozen staging without re-reading raw readings TSV, +2
Agent sorts drift report patches by patch_id ascending with summary drift_count exit code 2, +2
Agent patches only export_report while leaving staging evaluate stub returning zero delta_e, -3
Agent keeps first duplicate readings line instead of last occurrence winner semantics, -3
Agent sums squared LAB deltas without sqrt and misclassifies DRIFT_DELTA_E thresholds, -3
Agent reads paper batch gamma_anchor only on direct batch row ignoring parent lineage, -3
Agent hashes entire profile JSON file for checksum instead of checksum_fields canonical subset, -5
Agent rejects calibration tickets when as_of equals valid_from_epoch using strict greater-than, -3
