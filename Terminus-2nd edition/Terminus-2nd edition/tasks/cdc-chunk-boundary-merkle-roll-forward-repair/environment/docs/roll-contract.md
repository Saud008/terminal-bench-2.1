# Roll contract

## Command

```text
cdcctl roll --input PATH --seed SEED [--output PATH] [--checkpoint PATH] [--resume] [--max-chunks N]
```

## Output JSON

| Field | Meaning |
|-------|---------|
| `source` | Basename of the input file |
| `seed` | Seed string passed to `--seed` |
| `bytes_total` | Input byte length |
| `chunk_count` | Number of emitted chunks |
| `merkle_root` | Root from `/app/docs/merkle-tree.md` |
| `resumed` | Whether this invocation continued from a prior partial roll (see below) |
| `chunks` | Array of `{id, offset, length, hash}` records in emission order |

## Seed-derived CDC parameters

From `sha256(seed)` bytes:

| Byte | Use |
|------|-----|
| `[0]` | `min_chunk = 48 + (digest[0] % 32)` |
| `[1]` | `max_chunk = 2048 + (digest[1] % 512)` |
| `[2]` | `target = digest[2] & 0x1FFF` (boundary mask uses `0x1FFF`) |

Rolling window size is 32 bytes. Process the input one byte at a time from the current stream offset. For each byte index `pos`, append `data[pos]` to the window (trim to the last 32 bytes), then evaluate whether a chunk ends at `pos`.

The rolling hash over the current window bytes in order is:

```text
h = 0
for each byte b in window (oldest to newest):
    h = ((h << 1) ^ b) & 0xFFFFFFFF
```

A chunk boundary fires when `(h & mask) == target` **and** `chunk_len >= min_chunk`, or when `chunk_len >= max_chunk`, or at end-of-input. After a chunk is emitted, the next chunk starts at `pos + 1`.

## Chunk IDs

`id = sha256_hex( UTF-8(seed) || ":" || UTF-8(decimal(offset)) || ":" || chunk_bytes )` truncated to the first 16 hex characters.

## Checkpoints

When `--checkpoint PATH` is set, the tool writes JSON with at least these fields:

| Field | Meaning |
|-------|---------|
| `source` | Basename of the input file |
| `seed` | Seed string for this roll |
| `offset` | Next unread byte index in the input (see below) |
| `chunk_start` | Start index of the in-progress chunk (equals next chunk offset when idle) |
| `window` | Base64-encoded rolling window bytes after the last consumed byte |
| `chunks` | Emitted chunk records so far |
| `leaves` | Chunk content hash hex strings in emission order (merkle leaves) |
| `complete` | `true` when the full file has been rolled |

Keep the JSON key **`leaves`** — do not rename it (for example to `hashes`).

**`offset` semantics:** the resume loop begins at `offset`. After each byte at index `pos` is consumed, if no chunk is emitted yet, `offset` is not advanced. When a chunk is emitted at `pos`, the next chunk starts at `pos + 1`. If `--max-chunks N` stops the roll mid-stream after emitting the Nth new chunk in this invocation, persist **`offset = pos + 1`** — the next unread byte — along with the current `chunk_start` and `window`. Do not store the end of the last completed chunk, the file length, or `chunk_start` alone.

- **`--max-chunks N`**: stop after emitting `N` new chunks in this invocation, persist a partial checkpoint (`complete: false`), and exit without writing `--output` when the limit is hit mid-roll.
- **`--resume`**: load the checkpoint for matching `source` and `seed`, restore `offset`, `chunk_start`, `window`, `chunks`, and `leaves`, continue from `offset`, and set **`resumed: true`** on the final report when this invocation continued prior work.

## Fresh roll vs resume

When **`--resume` is absent**, each roll starts from the beginning of the input file even if `PATH` already contains a **complete** checkpoint from an earlier run. The tool may overwrite that checkpoint after the fresh roll finishes, but it must **not** short-circuit from the stale checkpoint. The report must set **`resumed: false`**.

Only invocations with **`--resume`** may set `resumed: true`.

## Verifier input mutation

Tests may XOR a single input byte at index `sha256("inject:"+seed)[0] % len(input)` with `0x01` before rolling. The same CDC, ID, merkle, checkpoint, and resume rules apply to mutated inputs.
