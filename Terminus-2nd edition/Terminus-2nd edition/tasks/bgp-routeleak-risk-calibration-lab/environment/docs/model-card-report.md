# Model-card report

Write /app/state/eval-snapshot.json first with fields:
- schema_version (1)
- run_id
- experiment
- feature_scale
- selected_threshold
- split_counts {train, validation, test}
- rows: list of {example_id, peer_group, split, label, score, predicted} in input file order

Then write the sealed report to --report with:
- schema_version (1)
- run_id
- experiment
- selected_threshold
- validation_fbeta
- test_confusion {tp, fp, tn, fn}
- test_brier
- test_ece
- feature_names (copy from model)
- audit_digest — sha256 hex of newline-joined lines `example_id|split|label|score:.6f|predicted` for snapshot rows in snapshot order (not re-sorted).

Round floating metrics in the report to 6 decimal places as strings are not required; JSON numbers are fine if within 1e-9 of reference.
