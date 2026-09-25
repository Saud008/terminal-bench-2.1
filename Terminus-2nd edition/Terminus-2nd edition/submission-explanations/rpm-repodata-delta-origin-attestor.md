# Submission explanations — rpm-repodata-delta-origin-attestor

**Task folder:** tasks/rpm-repodata-delta-origin-attestor/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must wire an offline RPM repository attestor where repomd checksum verification, NEVRA lineage ranking, modulemd default streams, and mirror snapshot staleness all feed a single staging snapshot before export. Each layer uses a different contract document under /app/docs/, and fixing only repomd SHA-256 verification still leaves epoch-less NEVRA strings, wrong module streams, stale mirror acceptance, and an incorrect origin digest. The lineage fixture deliberately traps ASCII version sorting versus RPM EVRA ordering when 10.1 must outrank 9.99. Hidden tb3-gamma packages and module rows force general parsing instead of hardcoded widget names or bundled checksum literals. Partial fixes that patch export digest alone still fail because staging ingest must populate mirror_repo_revision and ranked nevra rows coherently. Export must read staging only, so agents cannot re-open mirror manifests during attestation and hope ingest bugs remain hidden.

## Solution Explanation

The oracle patches six bash modules on the working baseline: repomd checksum type routing, primary NEVRA epoch formatting, modulemd stream_name extraction, mirror revision and timestamp validation, EVRA lineage ranking during staging ingest, and sha256 canonical digest export. The rpm-repo-attest CLI ingests fixture repos with an explicit mirror manifest argument, writes /app/state/repo-stage.json, then exports /app/output/repo-attestation.json without re-parsing repodata from the repository tree. Staging records checksum_ok, mirror_snapshot_valid, ranked packages, module defaults, and ingest_seq for deterministic replay. Independent reference_attest.py recomputes the export document from staging bytes for anti-cheat comparison across bundled and hidden repositories. The decoy lib module is intentionally off the hot path and must not be edited for a correct export.

## Verification Explanation

Pytest drives the bash CLI via subprocess for ingest and export on baseline, lineage, and /opt/verifier-fixtures/repos/tb3-gamma trees. Tests assert checksum_ok, mirror_snapshot_valid, lineage_rank, module defaults, sorted nevra output, and origin_digest against reference_attest without embedding hidden package names in the environment source. Partial-fix trap cases restore broken lib snapshots and prove single-module golden patches still fail independent reference export. A staging mutation test confirms export honors mirror_snapshot_valid from repo-stage.json rather than re-reading live mirror files. Twenty-four behavioral tests include two hidden-trap cases and rebuild bash modules through verifier-rebuild.sh before pytest executes.
