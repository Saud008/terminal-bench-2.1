# Submission explanations — nextflow-channel-resume-cache-auditor

**Task folder:** tasks/nextflow-channel-resume-cache-auditor/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must implement a three-stage Go CLI that ingests Nextflow-like run directories, stages normalized task rows, audits resume-cache invariants, and exports an unsafe-cache rollup. Difficulty comes from interacting contracts: lexicographic glob expansion feeds expansion_hash, container digests need case-insensitive normalization, and lineage_digest must chain parent hashes root-first before the task hash. Audit rules cross-cut cached flags, retry attempts, prior exit status, and cross-run cache marker sessions documented separately from the short instruction. Partial fixes pass bundled scenarios but fail hidden traps where poisoned glob directories or digest drift require every layer to be correct.

## Solution Explanation

The oracle rebuilds nfresume-audit after patching ingest, globexpand, digest, lineage, audit rules, provenance checks, and export generation gating, then runs ingest → audit → export for every bundled scenario so sealed reports under /app/output are produced end-to-end. Ingest reads trace JSON and run.meta.json, expands globs sorted, normalizes digests, computes lineage and expansion hashes, and writes /app/state/resume-stage.json. Audit evaluates digest drift, glob mismatch, lineage break, retry stale cache, and provenance crossrun into sorted findings with a canonical audit_digest. Export refuses to run until audit-generation.json matches staging and copies findings into the report schema under /app/output.

## Verification Explanation

Pytest drives nfresume-audit via subprocess over bundled and /opt/verifier-fixtures/nfresume scenarios without hardcoded task ids or digests in assertions. An independent reference_audit module recomputes staging fields and unsafe findings from fixture run directories. Tests verify staging path contracts, per-rule flags, hidden TB3 traps, persistence generation gates, and full export equality against the reference including audit_digest. test.sh rebuilds the Go binary before pytest so verifier exercises the agent-compiled artifact.
