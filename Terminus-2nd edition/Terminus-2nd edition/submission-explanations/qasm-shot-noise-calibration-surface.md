# Submission explanations — qasm-shot-noise-calibration-surface

**Task folder:** tasks/qasm-shot-noise-calibration-surface/
**Platform form only** — not in upload zip.

## Difficulty Explanation

This task is marked hard because qasmenv ties shot histogram normalization, mitigation matrix selection, seed manifest provenance, readout drift correction, and Wilson uncertainty export into one numeric pipeline spread across five docs under /app/docs/. Each behavior lives in a different Rust module, so fixing per-row normalization alone still leaves matrix tie-breaks, drift math, and digest serialization wrong on hidden verifier fixtures with alternate qubit labels and larger mitigation matrices. Wilson intervals must use mitigated probabilities after matrix application and drift renormalization, not raw histogram fractions, which is a common partial-fix trap. Export digest binding requires a compact JSON payload with sorted envelope keys and nested intervals per qubit, so agents who patch compute but serialize a top-level intervals field still fail digest bytes even when envelope math is correct. Twenty-four behavioral tests plus seed offset environment overrides require all six interacting layers to agree before the independent reference cross-checks pass.

## Solution Explanation

The oracle copies six corrected Rust modules into /app, rebuilds qasmenv, and runs stage ingest, envelope compute, and report export in order. Ingest writes the authoritative cal-staging snapshot with histogram rows, mitigation candidates, drift factors, and seed manifest metadata while compute reads staging only to produce the envelope ledger. Histogram rows normalize by their own sums, matrix selection breaks priority ties with the seed hash prefix rule including optional seed offset overrides, and provenance chains sort alphabetically before digest binding. Readout drift multiplies normalized probabilities per qubit with row renormalization, mitigation applies the selected matrix, and Wilson half-widths derive from mitigated values and total shots. Report export writes shot-noise-envelope.json and hashes the canonical payload with sorted envelope keys and nested intervals per uncertainty-interval-export.md.

## Verification Explanation

Pytest runs twenty-four behavioral cases after test.sh rebuilds qasmenv via cargo and installs the binary to /app/bin. Every test invokes the CLI through subprocess with fresh state paths, and reference_envelope.py independently recomputes normalization, matrix selection, drift, mitigation, Wilson intervals, and SHA-256 digest from the same JSON contracts. Bundled calibration files under /app/data/ exercise two-qubit histograms and tied-priority matrix selection, while dedicated tests assert cal-staging.json fields before ledger and export checks. Hidden verifier fixtures under /opt/verifier-fixtures/qasmenv/ supply alternate qubit labels, larger mitigation matrices, and seed offset tie-break overrides that bundled data cannot satisfy alone. Byte-level digest comparisons and full-pipeline reference equality catch compute-only or export-only shortcuts that would not survive a second report export.
