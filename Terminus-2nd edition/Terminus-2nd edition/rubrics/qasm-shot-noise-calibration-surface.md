# Platform rubric — qasm-shot-noise-calibration-surface

**Task folder:** tasks/qasm-shot-noise-calibration-surface/

Agent normalizes each qubit histogram row by its own row sum to unit probability, +3
Agent selects mitigation matrix by priority then seed manifest hash tie-break rule, +3
Agent sorts provenance chain entries alphabetically before ledger digest binding, +2
Agent applies readout drift as multiplicative per-qubit factors with row renormalization, +3
Agent computes Wilson uncertainty intervals from mitigated probabilities and shot counts, +3
Agent serializes export digest with sorted envelope keys compact JSON and nested intervals per qubit, +2
Agent includes provenance block in export digest ledger per uncertainty-interval-export doc, +2
Agent rebuilds qasmenv after editing histogram mitigate drift or export crates, +2
Agent reads envelope ledger during report export not raw calibration files, +2
Agent edits decoy envelope helpers expecting report export fix, -3
Agent divides histogram counts by global total instead of per-qubit row sums, -3
Agent picks mitigation matrix without seed hash tie-break when priorities tie, -2
Agent applies readout drift additively to normalized probabilities, -2
Agent omits provenance block from envelope digest ledger, -3
