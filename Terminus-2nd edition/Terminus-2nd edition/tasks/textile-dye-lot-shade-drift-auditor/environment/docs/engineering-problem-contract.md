# Engineering problem contract

Textile shade drift auditing is a colorimetry metrology problem, not a generic data pipeline repair task.

Reasoning path for agents:

1. Reconcile measured LAB tuples with inherited target_lab anchors after walking parent_batch_id genealogy.
2. Rank recipe sheets by effective_from_epoch at each batch created_at_epoch and pick the latest still-effective version.
3. Sort duplicate reading_id rows by file order and keep the final occurrence before delta evaluation.
4. Propagate rework window bounds across measured_epoch to choose pre-rework versus post-rework recipe targets.
5. Invariant: export-report must read correlated correlation snapshot JSON only; drift row sort order is batch_id then reading_id for audit_digest.

Distinctive failure modes: missing sqrt in CIE76, earliest-recipe pick instead of latest effective sheet, flat batch lookup without genealogy walk, exclusive rework_end_epoch, and export re-reading raw TSV instead of correlation-snapshot-only snapshots.

Primary artifact: shade drift report JSON under /app/output with audit_digest over sorted drift rows.
