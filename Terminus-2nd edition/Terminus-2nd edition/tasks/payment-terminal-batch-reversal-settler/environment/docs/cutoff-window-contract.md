# Cutoff window contract

Each scenario defines cutoff_event_ms. Transactions with event_ms less than or equal to cutoff_event_ms are included in the batch journal.

Transactions with event_ms strictly greater than cutoff_event_ms are excluded before sequence assignment.

Boundary inclusion: a transaction whose event_ms equals cutoff_event_ms is included.
