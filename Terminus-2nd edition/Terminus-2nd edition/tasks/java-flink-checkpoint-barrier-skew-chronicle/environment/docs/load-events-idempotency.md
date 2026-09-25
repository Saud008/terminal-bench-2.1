# load-events idempotency

Duplicate suppression key is the concatenation:

checkpoint_id + "|" + attempt_id + "|" + operator_id + "|" + subtask_index + "|" + event_kind + "|" + timestamp_ms

Keys scoped per attempt_id. Retried checkpoint attempts must not drop distinct lines that share checkpoint_id but differ in attempt_id.

Second load-events with identical input must write byte-identical event_index.json.
