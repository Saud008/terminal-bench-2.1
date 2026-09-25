# Ledger contract

The ledger tracks received `frame_seq` values per replay run.

- **playhead** — highest contiguous `frame_seq` starting from the smallest received sequence.
- **gaps** — inclusive ranges of missing received `frame_seq` values between the smallest seen sequence and playhead. **Recompute** these ranges from the full `seen` set after every processed frame; do not incrementally append or merge gap tuples while frames stream in. See **Received sequence gaps** below.
- **duplicate_acks** — count of frames whose `frame_seq` was already recorded. Duplicate frames must not alter **gaps** or **playhead** (ledger updates are idempotent for duplicates). **Sim inputs are not idempotent:** every received frame, including duplicate `frame_seq` resends, must still apply its parsed inputs to the sim.
- **peer_loss_gaps** — ranges decoded from each frame's `ack_base` + `loss_mask` (peer view of loss). See **Peer loss gaps** below.
- **frames_received** — total packets processed (includes duplicates).

After every processed frame, recompute **playhead** and received-sequence **gap tuples** from the full `seen` set. A duplicate `frame_seq` does not change `seen`, so duplicates must not alter the recomputed gaps or playhead.

## Received sequence gaps

Received-sequence gap tracking is a **two-stage** process: recompute from `seen` after each frame, merge once at export.

### Stage 1 — recompute after each frame

Once `seen` and playhead are updated for the frame, scan from `min(seen)` through playhead. Collect every inclusive run of `frame_seq` values that are not in `seen`. **Replace** the in-memory received-gap tuple list with the result of this scan. Do not carry forward tuples from earlier frames, do not append hole-by-hole, and do not merge ranges during the scan.

### Stage 2 — merge at export only

When writing the replay export JSON, run **one global merge** over the final recomputed received-gap tuple list (same merge algorithm as **peer_loss_gaps** below) and emit the result as `ledger.gaps`.

## Peer loss gaps

Peer loss reporting is a **two-stage** process: decode per frame, merge once at export.

### Stage 1 — decode and accumulate (per frame)

For each processed frame, decode `loss_mask` with the algorithm in `/app/docs/wire-format.md` (Loss mask section). That yields zero or more inclusive `(start, end)` tuples for that frame only.

**Append every tuple to an internal list in frame-processing order.** Do not merge, coalesce, or normalize tuples during accumulation. Do not swap `start`/`end` to enforce `start <= end`.

Contiguous lost runs from the bit scan often produce tuples where **`start` is numerically greater than `end`**: the scan begins at bit 0 (`ack_base - 1`) and walks toward lower sequences, so the first lost sequence in a run becomes `start` and the last lost sequence in that run becomes `end`.

Example: `ack_base = 410`, `loss_mask = 0xf0` decodes to one tuple `(405, 402)` — sequences 405 down through 402 were lost. This tuple must be stored as-is, not rewritten to `(402, 405)`.

Across multiple frames, tuples accumulate in receipt order. For example, three frames might append `(403, 403)`, `(401, 401)`, `(405, 402)`, `(419, 419)`, `(417, 417)` before export.

### Stage 2 — merge at export only

When writing the replay export JSON, run **one global merge** over the accumulated peer-loss tuple list (same export-time merge algorithm as **Received sequence gaps**, Stage 2):

1. Sort tuples lexicographically by `(start, end)` — **without** normalizing each tuple first.
2. Walk sorted tuples. Merge the next tuple into the current range only when `next.start <= current.end + 1` (u32 wrapping). Otherwise flush the current range and start a new one.
3. Emit the merged list as `ledger.peer_loss_gaps`.

Because step 1 keeps descending-scan tuples such as `(405, 402)` unnormalized, the global merge can leave multiple adjacent entries that would collapse if tuples were min/max-normalized first. The `loss-bitmask` bundle exercises this behavior.

**Do not** merge peer-loss tuples after each frame, and **do not** normalize `(start, end)` pairs before the export-time merge.
