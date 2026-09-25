# Partition replay deduplication

Replay batches list job_keys to activate on a partition. When batch idempotent is true, the pair batch_id and job_key may activate at most once across the full replay.

Duplicate idempotent retries increment duplicate_activations_skipped and must not append a second activation_sequence entry for the same job_key.

Non-idempotent batches always attempt activation even when batch_id repeats.
