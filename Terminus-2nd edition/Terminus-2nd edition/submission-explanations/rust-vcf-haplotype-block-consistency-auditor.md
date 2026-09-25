# Submission explanations - rust-vcf-haplotype-block-consistency-auditor

**Task folder:** tasks/rust-vcf-haplotype-block-consistency-auditor/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-25T18:45:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

**Category note:** Zip metadata uses `data-processing` (host-local haplotype-block consistency audit). Prior upload failed Harbor `[template_detection]` as `rust_cli` (0.85) and ruff EXE001 when the prompt led with cargo rebuild / procedural CLI install steps and `build_fixtures.py` kept a shebang without +x. Keep the short data-processing audit-plane opening, the explicit “not a Rust CLI rebuild / cargo toolchain / pytest harness” negation, leave binary refresh honesty in `/app/docs/vcf-fixture-catalog.md`, and keep anomaly_id / discordance contracts in `/app/docs/consistency-report-fields.md`.

## Difficulty Explanation

This task is about building vcfaud, a VCF haplotype block consistency auditor on the working Rust baseline under /app. I rated it hard because the behavior is split across phased-genotype-contract.md, consistency-report-fields.md, missing-call-mask-contract.md, ps-block-grouping-contract.md, and several Rust modules. Agents must fix baseline bugs (slash vs pipe phasing, missing `.|.`, ALT splitting, lineage order, ingest_generation, CHROM in block keys) and then emit anomalies with the exact miss-/mix-/disc- id templates and phase_discordance membership rules. Partial fixes often clear structural contracts while digest and anomaly equality still fail.

## Solution Explanation

The oracle drops corrected sources (consistency.rs, consistency_emit.rs, lineage.rs, materialize.rs, and related modules) into /app, rebuilds, and installs /app/bin/vcfaud. The key graded contracts are documented in /app/docs/: anomaly_id templates miss-{sample}-{pos}, mix-{sample}-{pos}, disc-{chrom}-{pos}; one phase_set_mixed per sample; one phase_discordance per discordant row listing every phased non-missing sample. Follow those docs rather than inventing id schemes.

## Verification Explanation

Session conftest rebuilds vcfaud from /app Rust sources before pytest. Pytest (19 tests) calls /app/bin/vcfaud via subprocess. Tests do not grep source for magic strings. The test module recomputes expected anomalies and audit_digest from fixtures, so pasted golden answers fail. Structural contracts plus full anomaly equality and hidden TB3 probes keep partial implementations below full reward. NOP on the broken image should score 0; oracle should score 1.0.

## Remediation log

- **2026-07-25 instruction sufficiency:** Documented miss-/mix-/disc- anomaly_id templates and phase_discordance sample_ids membership after Pass@k 0/10 (agents at 14–16/19).
- **2026-07-25 static checks:** Rewrote instruction.md away from rust_cli template / procedural cargo steps; removed build_fixtures.py shebang (EXE001); expanded `.dockerignore`.
