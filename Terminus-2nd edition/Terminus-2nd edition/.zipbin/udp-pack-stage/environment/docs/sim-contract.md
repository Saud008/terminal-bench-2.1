# Sim contract

Deterministic tick sim driven by parsed inputs.

Opcodes:
- `0` — add `value` to `accumulator`
- `1` — `mix ^= tick * value`
- `2` — `accumulator *= max(value, 1)` (wrapping)
- other — `mix += value`

Each input applies immediately when its frame is processed, even when the frame's `tick_offset` set is not a contiguous `0..=max` batch.

Apply sim inputs for **every** received frame, including duplicate `frame_seq` resends. Ledger gap/playhead bookkeeping is idempotent on duplicates; sim application is not.

`tick` tracks the maximum tick seen. `state_hash` is SHA256 of `{client_id}:{seed}:{tick}:{accumulator}:{mix}:{inputs_applied}` formatted as colon-separated decimal strings.
