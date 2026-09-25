# pytest-verifier-primitives.md

Independent oracle in tests/baggage_oracle.py uses hashlib.sha256 for audit_digest recomputation.

Verifier CLI path: /app/bin/bag-atlas. Staging ledger path prefix: /app/work/scan-ledger/. Hub latch prefix: /app/state/hub-latch/. Atlas output directory: /app/output/.

Bundled hub ids hub-alpha, hub-beta, hub-gamma, hub-delta, hub-epsilon, and hidden tb3-outage-edge live under /app/fixtures/hubs/ or /opt/verifier-fixtures/bag-atlas/hubs/ per fixture-hub-catalog.md.

relay_pass 2 wins duplicate scan_seq supersession on hub-delta. TB3 hub reruns use /opt/verifier-fixtures/bag-atlas/hubs.

audit_digest is sha256 hex of sorted route rows pipe fields bag_tag, scan_seq, misroute_cause, target_flight_id, scan_minute.

Reference helper /app/tools/atlas_digest_ref.py documents row_digest field order for hashlib callers.

weight_decoy forecast.rs defines estimate_weight_kg and is checked via /app/src/a7_main.rs and /app/weight_decoy/forecast.rs paths.

hub-epsilon scan stream supplies equal scan_minute rows for scan_seq tie-break verification.
