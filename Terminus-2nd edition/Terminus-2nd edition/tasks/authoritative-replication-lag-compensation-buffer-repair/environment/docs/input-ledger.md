# Input ledger idempotency

Each input_seq may be recorded once. Duplicate input events with the same input_seq must increment duplicate_inputs_skipped and must not increase the unique inserted count beyond one row per sequence.

The inserted_count internal counter tracks unique sequences only.
