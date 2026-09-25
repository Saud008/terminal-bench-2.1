# Wire format (UDPI)

All multi-byte integers are **little-endian** unless noted.

| Offset | Size | Field |
|--------|------|-------|
| 0 | 4 | Magic `UDPI` |
| 4 | 4 | `client_id` u32 |
| 8 | 4 | `frame_seq` u32 |
| 12 | 4 | `ack_base` u32 |
| 16 | 8 | `loss_mask` u64 |
| 24 | 4 | `base_tick` u32 |
| 28 | 1 | `num_inputs` u8 |
| 29+ | 5×N | Inputs |

Each input: `tick_offset` u16, `opcode` u8, `value` i16.

## Sequence space

`frame_seq` and `ack_base` use **u32** modular arithmetic. `a` is before `b` when `(b - a) mod 2³²` is in `(0, 2³¹)`.

## Loss mask

`loss_mask` is **little-endian** u64. Bit *i* set means sequence `ack_base - 1 - i` was lost on the peer side.

### Decoding `gaps_from_mask(ack_base, loss_mask)`

Scan bits `i = 0..63` in ascending order (bit 0 is the sequence immediately before `ack_base`). For each bit:

- If set, extend the current lost run (start the run at this sequence when none is open).
- If clear and a run is open, close it with `end = ack_base - 1 - i + 1` (the sequence just above the cleared bit) and append `(start, end)`.
- After bit 63, if a run is still open, append `(start, ack_base - 64)`.

Tuples are emitted in bit-scan order. A multi-bit lost run yields **`start` greater than `end`** because sequences decrease as `i` increases. Preserve that ordering; do not rewrite tuples to enforce `start <= end`.

Ledger accumulation and export-time merging are defined in `/app/docs/ledger-contract.md` (**Peer loss gaps**).
