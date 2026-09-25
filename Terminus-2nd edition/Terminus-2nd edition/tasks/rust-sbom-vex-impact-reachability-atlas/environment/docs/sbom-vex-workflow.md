# SBOM VEX workflow

vexatlas implements bundle capture followed by impact roll-up for supply-chain audits.

CLI surface:

  vexatlas capture --bundle <bundle.json>
  vexatlas rollup --output <path>

Exit codes: success 0, unreadable bundle 2, rollup before capture 3.

Bundle capture loads bundle.json, canonicalizes CycloneDX package URLs, copies runtime adjacency rows, stores OpenVEX statements with RFC3339 expiry timestamps, and writes snapshot file /app/state/waiver-snapshot.json during capture.

Impact roll-up reads waiver-snapshot.json only. It must not reopen bundle.json from disk. Roll-up walks transitive runtime exposure from each binary anchor package, resolves effective OpenVEX status per exposed package and vulnerability id, attaches waiver evidence when a not_affected or fixed statement applies, and writes exposure-ledger.json.

Run capture before roll-up for the same bundle_id. Roll-up without prior capture exits code 3.

Cross-run state lives in run-seq file /app/state/run-seq.json where ingest_seq is stored. Unchanged bundle fingerprints must not advance run_seq.

Reset state with /app/scripts/reset-state.sh before deterministic cross-run checks in verifier tests.
