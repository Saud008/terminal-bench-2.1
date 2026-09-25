# Submission explanations — modbus-register-scaling-drift-cataloger

**Task folder:** tasks/modbus-register-scaling-drift-cataloger/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must implement a Go Modbus poll cataloger where low-level register decoding and temporal device policy interact before any drift report is published. Signed 32-bit values depend on word order rules that manifest overrides can change per register, while scale revision epochs bind to poll receipt time rather than the device clock stamped on the frame. Stale clock skew rejection, alarm suppression windows, and baseline drift alarms each consult different manifest sections spread across eight documents under /app/docs/. Ingest writes a staging snapshot with a frames digest and manifest path that catalog and export must honor, so partial fixes to decode or export alone still fail hidden gamma fixtures and seed-parametrized scaling cases.

## Solution Explanation

The oracle copies golden Go modules for staging ingest, word-order decode, scale epoch selection, clock skew rejection, alarm suppression, manifest overrides, catalog assembly, and export gates into /app/internal/, then rebuilds modbusctl with go build. The core insight is that engineering values come from raw registers after word-order and override resolution, scaled by the epoch whose effective_ms is latest but not after received_ms. Frames exceeding clock skew limits land in rejected-frames.jsonl instead of the catalog. Suppression windows clear drift_alarm even when drift exceeds threshold. Export validates the staging digest and non-zero catalog generation before writing drift-catalog.json with a catalog_digest computed from sorted JSON excluding the digest field itself.

## Verification Explanation

Pytest rebuilds modbusctl in test.sh and drives ingest, catalog, export, and run through subprocess on every case. reference_catalog.py independently decodes frames, applies manifest policy, and recomputes drift catalogs and rejection lists from the same fixtures. Tests assert poll-staging paths, staging-seq increments, generation gates, tampered digest rejection, and decoy module isolation. Two hidden tests replay the gamma fixture tree mounted at /opt/verifier-fixtures/modbus-gamma/. Parametrized seeds mutate register baselines and scale factors with temporary manifest files to block hard-coded engineering totals.
