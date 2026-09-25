# Submission explanations — icc-softproof-gamut-drift-bundler

**Task folder:** tasks/icc-softproof-gamut-drift-bundler/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must implement a three-stage ICC softproof drift bundler where numeric color science, provenance, and policy precedence interact across separate Bash modules. CIE76 LAB delta math must use the full Euclidean formula while rendering-intent selection follows a strict precedence list against per-intent reference patches. Paper batch lineage requires walking parent links to inherit gamma anchors, and profile checksum validation must hash only the documented checksum_fields subset rather than the entire JSON file. Calibration ticket epochs gate patch validity with inclusive boundary comparisons at the evaluated unix timestamp. Partial fixes to export alone still emit empty drift summaries while staging evaluation remains stubbed, and duplicate patch rows punish agents that keep the first TSV line instead of the last.

## Solution Explanation

The oracle patches nine cooperating libraries plus ingest, evaluate, and export scripts and the icc-drift-bundler CLI wrapper. Ingest parses spectrophotometer TSV into a staging snapshot beside the readings path and records readings digests in the run registry. Evaluate enriches staging with per-patch delta_e, active intent, inherited gamma, ticket ids, and drift flags using the policy and ticket fixtures. Export reads only the frozen staging evaluation block, validates schema via the stage helper, writes the drift report JSON, and exits 2 when drift_count is positive. A decoy legacy_gamut module ships off the hot path to trap agents that patch decorative helpers instead of the export pipeline.

## Verification Explanation

Pytest drives the Bash CLI through subprocess on every scenario and compares outputs to an independent reference_drift oracle that recomputes LAB deltas, lineage gamma, checksums, and ticket validity in Python. Bundled seed fixtures cover drift on patch P-200, inherited gamma on PB-CHILD, and digest propagation into the exported report. Randomized patch ids and LAB triples in tmp_path runs block hard-coded answers. Hidden TB3 fixtures under /opt/verifier-fixtures/icc supply alternate profiles and readings not listed in the public catalog. Partial-module traps swap single broken libraries from /opt/verifier-broken-icc to ensure staging-stub, parse-order, and export-only edits fail while the full golden pipeline passes after solve.sh applies all patches.
