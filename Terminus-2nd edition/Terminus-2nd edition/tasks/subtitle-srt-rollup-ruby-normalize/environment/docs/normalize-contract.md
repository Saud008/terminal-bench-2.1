# Normalize integrity contract

Host-local authenticity admission and sealed export rules for the field-log chronology-admission control plane. See `/app/docs/srtctl-ops-workflow.md` for integrity scope.

`srtctl normalize --in <path> --seed <seed> --fixture <name> --export <json>` writes a single JSON document through a **two-stage** pipeline documented in `/app/docs/normalize-snapshot.md`. Stage 1 writes a normalize snapshot and sealed ledger under `/app/state/srtctl/`; stage 2 reads that snapshot (never re-parses the source SRT) and applies roll-up export.

## Pipeline order

1. **Parse** the input SRT (see `/app/docs/srt-format.md`).
2. **Apply seed offset** — add `seed_offset_ms` to every cue `start_ms` and `end_ms`.
3. **Resolve overlaps** — sort by `(start_ms, source_index)`; when cue *B* starts before cue *A* ends, trim *A*’s `end_ms` to *B*’s `start_ms` (touching cues where `end == start` are allowed).
4. **Apply ruby shifts** — for cues containing `{\an8}`, extend each ruby segment end by 250 ms, capped at cue end.
5. **Roll-up export** — merge consecutive cues into one exported cue when the gap between the previous end and next start is ≤ `rollup_gap_ms` (120 ms) **and** the previous cue text does not end with `.`, `!`, or `?`. Roll-up joins the next cue’s display text onto the previous exported cue with a **single ASCII space** (`" "`) between the two strings (not a newline), extends the previous end time, marks the previous as `rolled_up: true`, and **does not** emit a separate cue for the absorbed line.

## Seed offset

```
seed_offset_ms = 50 + (fnv1a64(seed) % 450)
```

Use 64-bit FNV-1a over UTF-8 seed bytes with offset basis `0xcbf29ce484222325` and prime `0x100000001b3`.

## Export JSON schema

| Field | Type | Meaning |
|-------|------|---------|
| `fixture` | string | `--fixture` argument |
| `seed` | string | `--seed` argument |
| `seed_offset_ms` | u32 | computed offset |
| `format` | string | always `srt-normalized-v1` |
| `cues` | array | exported cues after roll-up |
| `stats` | object | counters (below) |

Each cue object:

| Field | Type | Meaning |
|-------|------|---------|
| `index` | u32 | 1-based export index after roll-up |
| `source_index` | u32 | index line from the source file |
| `start_ms` | u32 | after offset, overlap trim, before roll-up merge |
| `end_ms` | u32 | after offset, overlap trim, roll-up may extend |
| `text` | string | display text with `{\an8}` and `{rt}` markers removed |
| `ruby_segments` | array | `{base, reading, start_ms, end_ms}` |
| `rolled_up` | bool | true if this export row absorbed a later cue |

Stats object:

| Field | Meaning |
|-------|---------|
| `parsed` | cues read from file |
| `exported` | cues in export array |
| `overlap_trims` | count of end-time trims |
| `rollup_removals` | count of cues absorbed by roll-up |
| `ruby_shifts` | count of ruby segments whose end was extended |

## Constants

- `ruby_shift_ms = 250`
- `rollup_gap_ms = 120`

## Text cleanup

Within a single source cue, export `text` joins that cue’s source lines with `\n`, strips `{\an8}`, and removes `{rt}` markers while preserving base characters for ruby parsing. **Roll-up** between separate cues uses a single ASCII space between the previous and next display strings (see step 5), not `\n`.
