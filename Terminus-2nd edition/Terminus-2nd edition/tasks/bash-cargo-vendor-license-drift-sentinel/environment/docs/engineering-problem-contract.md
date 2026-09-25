# SPDX vendor compliance engineering contract

Objective: operate a vendored Cargo compliance ledger that inventories lock metadata, attests license and checksum drift, and publishes deterministic attestations for downstream policy gates.

The baseline governor mishandles duplicate lock stanzas, mis-orders SPDX precedence, formats checksum payloads incorrectly, drops patch lineage findings, narrows workspace fingerprints, and re-reads vendor during publish.

Observable failures include missing duplicate version rows, false clean license rows, silent patch overrides, unstable audit digests, and poisoned vendor trees altering published CSV and JSON outputs.
