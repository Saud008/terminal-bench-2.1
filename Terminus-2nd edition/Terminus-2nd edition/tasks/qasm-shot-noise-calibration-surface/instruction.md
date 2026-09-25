Task identity eb9951dda4 defines the engineering problem for qasm shot noise calibration surface. See /app/docs/engineering-problem-contract.md for root cause and failure mode contracts.

Implement the qasmenv shot-noise calibration envelope tool on the working Rust baseline under /app. The tool ingests calibration histograms and QASM experiment descriptors, writes a normalized staging snapshot at /app/state/cal-staging.json, computes mitigated shot-noise envelopes with uncertainty intervals into /app/state/envelope-ledger.json, and exports the final report to /app/output/shot-noise-envelope.json with companion digest at /app/output/envelope-digest.txt

Your work must satisfy every contract cited below. The src/decoy module is not on the stage ingest, envelope compute, or report export hot path and must not be edited for a correct export.

Build /app/bin/qasmenv from the workspace root. Subcommands:

  qasmenv stage ingest --cal-dir DIR --qasm PATH --manifest PATH
  qasmenv envelope compute
  qasmenv report export

After stage ingest, /app/state/cal-staging.json must record ingest_seq, the seed manifest, parsed qasm gate count per /app/docs/qasm-gate-counting.md, per-qubit histogram rows, mitigation matrix candidates, and readout drift factors from the calibration directory.

Histogram normalization must follow /app/docs/shot-histogram-normalization.md: each qubit row is divided by its own row sum so probabilities per qubit sum to one.

Mitigation matrix selection must follow /app/docs/mitigation-matrix-selection.md: among candidates matching the qubit count dimension, pick highest priority; when priorities tie, break ties using the seed manifest hash prefix rule documented there.

Provenance binding must follow /app/docs/seed-manifest-provenance.md: the provenance chain entries are sorted alphabetically before digest binding into the ledger.

Readout drift correction must follow /app/docs/qubit-readout-drift.md: drift factors multiply normalized probabilities per qubit, then each qubit row is renormalized.

Uncertainty intervals must follow /app/docs/uncertainty-interval-export.md: Wilson score half-widths are computed from mitigated probabilities and total shot counts, not pre-mitigation values.

report export reads the envelope ledger only. It writes /app/output/shot-noise-envelope.json and derives /app/output/envelope-digest.txt from the canonical export digest payload in /app/docs/uncertainty-interval-export.md including the provenance block.

Bundled fixtures use /app/data/. Hidden verifier fixtures may supply alternate qubit labels, matrix dimensions, and TB3_SEED_OFFSET at runtime under /opt/verifier-fixtures/qasmenv/
