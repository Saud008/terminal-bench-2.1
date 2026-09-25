# srtctl integrity workflow — host-local chronology-admission control plane

This task is a **security** host-local srtctl chronology-admission control plane. Integrity operators admit heterogeneous SRT field logs under authenticity gates into a temporally closed export with tamper-evident stage artifacts and digest-sealed ledgers. The working baseline under /app must keep admission authenticity, stage barriers, and sealed ledger attestation aligned; it is not a generic service repair exercise.

## Ops scope

| Stage | Closure invariant | Reference |
|-------|-------------------|-----------|
| Seed offset | Deterministic chronology shift from UTF-8 seed bytes | `/app/docs/normalize-contract.md` |
| Overlap trim | Non-negative cue durations after pairwise end-time closure | `/app/docs/normalize-snapshot.md` |
| Ruby caps | Segment end extensions bounded by cue end after overlap closure | `/app/docs/normalize-contract.md` |
| Roll-up merge | Gap tolerance merge with space-joined display text | `/app/docs/normalize-contract.md` |
| Ledger seal | FNV-1a64 digest binds snapshot bytes to export sequence | `/app/docs/normalize-export-seq.md` |

## Two-stage temporal pipeline

Stage 1 persists post-ruby cues in `normalize-snapshot.json` and seals `normalize-ledger.json`. Stage 2 reads staged cues only (never re-parses source SRT) and emits roll-up export JSON. Stage order is fixed: overlap resolution before ruby shifts so ruby segment caps use overlap-trimmed cue ends.

## Deliverables

- Export JSON at the caller `--export` path (`format: srt-normalized-v1`)
- Snapshot and ledger artifacts under `/app/state/srtctl/<fixture>-<seed>/`
- Monotonic `export_seq` with byte-identical repeat exports per `/app/docs/normalize-export-seq.md`
- Correct Rust sources under `/app/crates/` so a release rebuild of `srtctl` implements the contracts above
