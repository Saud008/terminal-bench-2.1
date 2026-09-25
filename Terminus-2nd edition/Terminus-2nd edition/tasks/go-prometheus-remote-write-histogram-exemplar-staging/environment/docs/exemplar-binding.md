# Exemplar binding

Exemplars carry a `le` label matching a histogram bucket boundary. Bind each exemplar trace ID to the bucket with the same `le` value.

When `counter_reset` is true for a series, drop all exemplars before binding. Bound trace IDs must be empty after a counter reset.
