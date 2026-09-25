Field-log integrity operators run the host-local srtctl chronology-admission control plane at /usr/local/bin/srtctl. Each offline trust pass admits SRT field-log fixtures under seed-offset chronology authenticity, overlap-trim closure barriers, and ruby segment timing caps; stages a tamper-evident snapshot and digest-sealed ledger under /app/state/srtctl/<fixture>-<seed>/; and publishes a digest-bound roll-up export JSON (format srt-normalized-v1) only from that staged state without re-parsing source SRT. There is no remote caption cluster. Integrity contracts: /app/docs/srtctl-ops-workflow.md, /app/docs/normalize-contract.md, /app/docs/normalize-snapshot.md, /app/docs/normalize-export-seq.md, /app/docs/srt-format.md, and /app/docs/fixture-catalog.md.

Repair the Rust workspace under /app/crates/ so a release rebuild of package srtctl succeeds and implements the contracts above. Graded checks rebuild from those sources with `cargo build --offline --release --locked -p srtctl` and replace /usr/local/bin/srtctl; editing only the installed binary is discarded. Required sources include:

  /app/crates/srtctl/
  /app/crates/srt-core/src/runner.rs
  /app/crates/srt-core/src/ledger.rs
  /app/crates/srt-core/src/publish.rs
  /app/crates/srt-core/src/parser.rs
  /app/crates/srt-core/src/ruby.rs
  /app/crates/srt-core/src/ssrrn_timeline.rs
  /app/crates/srt-core/src/rollup.rs

Primary artifacts:

  /app/state/srtctl/<fixture>-<seed>/normalize-snapshot.json — tamper-evident stage-1 cues after overlap and ruby gates
  /app/state/srtctl/<fixture>-<seed>/normalize-ledger.json — digest-sealed ledger bound to snapshot bytes and export_seq
  caller --export path — sealed roll-up JSON bound to staged cues only

Integrity constraints that must hold for every successful normalize:

- Seed chronology offset follows FNV-1a over UTF-8 seed bytes per /app/docs/normalize-contract.md.
- Overlap-trim closure completes before ruby segment caps so ruby ends use trimmed cue ends.
- Stage-2 export reads staged cues only; source SRT must not be re-parsed for export.
- Export schema, cue fields, and ledger digests match /app/docs/normalize-contract.md and /app/docs/normalize-snapshot.md.
- export_seq is monotonic under /app/state/srtctl/epochs per /app/docs/normalize-export-seq.md.
- For an unchanged fixture and seed, sealed ledger digests and export JSON are byte-identical across fresh runs that start with empty /app/output/ and /app/state/srtctl/epochs.

Operator surface:

  srtctl normalize --in PATH --seed SEED --fixture NAME --export PATH

Bundled fixtures and seeds live under /app/fixtures/catalog.json and /app/fixtures/seeds.json (for example alpha01, beta17, gamma99). Do not edit /app/docs/, /app/fixtures/, or /tests/.
