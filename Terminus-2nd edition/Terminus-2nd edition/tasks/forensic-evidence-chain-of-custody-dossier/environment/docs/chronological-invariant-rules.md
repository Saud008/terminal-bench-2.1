# Chronological invariant rules

For each evidence_id, event_epoch_ms values must strictly increase across all event types.

Decreasing or equal event_epoch_ms values emit chronology_violation.
