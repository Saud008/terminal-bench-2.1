# Submission explanations — rust-cranelift-ir-register-pressure-atlas

**Task folder:** tasks/rust-cranelift-ir-register-pressure-atlas/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must implement a two-stage fluxpress neutron-spectrometer residual-occupancy lab where accrue-residuals fuses piecewise-linear background subtraction, micron-eV round-half-away-from-zero quantization, inclusive coincidence-veto gating, and energy-ordered persistence into one fluence ledger under /app/scratch/ring-fluence/, then emit-occupancy derives occupancy peak, spill risk, rank ladder, and a canonical digest from that ledger alone. Eight interacting defects span background interpolation, rounding mode, sort order, veto matching, occupancy accounting, accrual epoch persistence, rank order, and digest key canonicalization. Fixing one module leaves partial atlases that pass some bundled cases but fail hidden verifier fixture traps or cross-run epoch checks.

## Solution Explanation

The oracle applies eight unified diffs under residual_kernel, quantize, energy_order, coincidence_veto, occupancy_scan, fluence_ledger, closure_rank, and digest_line, then rebuilds fluxpress. Background subtraction interpolates between sorted anchors instead of averaging anchor counts. Quantization rounds half away from zero, energy order sorts by quantized energy then channel_id, and veto windows compare quantized bounds inclusively. Occupancy scans survivor start points for maximum closed-interval overlap, accrual_epoch increments from the prior ledger, and closure rows sort by residual_counts descending. closure_digest hashes a canonical sorted-key body built through serde_json::Value so Rust and the independent Python reference agree byte-for-byte.

## Verification Explanation

Pytest rebuilds fluxpress from live sources and compares atlas JSON to an independent Python reference in fluxpress_validate.py through subprocess-driven accrue-residuals and emit-occupancy calls. Bundled ring bundles exercise veto, occupancy-peak, quantize-edge, rank-ladder, and aperture-boundary cases, while hidden bundles under /opt/verifier-fixtures/fluxpress probe spill and micron-scale overrides. Persistence tests assert accrual_epoch monotonicity, ledger-only emit after fixtures are moved aside, and byte-identical idempotent re-emit output.
