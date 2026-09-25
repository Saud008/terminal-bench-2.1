# Model weight lineage atlas

ML platform operators must publish a reproducible weight lineage atlas from safetensors shard catalogs before adapters ship to production. The working Rust package under /app/environment builds the release CLI documented in /app/docs/weight_audit_flow.md which scans catalog JSON against binary shard files, records validation rows in /app/var/xr7_journal.ndjson, and publishes /app/lineage/weight_lineage_atlas.json for governance review.

Implement the scan and publish subcommands documented in /app/docs/weight_audit_flow.md. The atlas must enforce payload-relative tensor spans, dtype byte sizing including BF16, payload-only shard fingerprints, case-insensitive LoRA parent hash binding, globally monotonic run_seq across catalogs, and stable violation sort sequence across repeated runs.

## Production workflow

Rebuild the release CLI with /app/environment/scripts/build_all.sh, run catalog-scan on bundled catalog JSON under /app/environment/registry/catalogs and weight shards under /app/environment/registry/weights to populate /app/var/xr7_journal.ndjson, then run atlas-publish to write /app/lineage/weight_lineage_atlas.json.

## Contracts (read before coding)

- /app/docs/manifest_format.md — catalog JSON schema and per-shard tensor specs
- /app/docs/safetensors_layout.md — eight-byte header length and payload section layout
- /app/docs/span_guard.md — payload-relative offset validation rules
- /app/docs/elem_layout_rules.md — per-dtype element byte widths including BF16
- /app/docs/payload_fingerprint.md — payload-only fingerprint scope
- /app/docs/parent_hash_bind.md — case-insensitive base_model_hash lineage matching
- /app/docs/lineage_report_contract.md — violation sort order and totals semantics
- /app/docs/hidden_fixture_override.md — XR7_CATALOG_ROOT and XR7_WEIGHT_ROOT alternate roots

Atlas output must list violations sorted by tensor then code, set totals.violation_count to the violations array length, and keep tensor_count aligned with journal rows per manifest_id.

- /app/docs/safetensors_lineage_problem.md — scope boundary vs array consolidators

Grading invokes the release CLI through subprocess after cargo rebuild; hardcoding journal or atlas JSON fails hidden /opt/verifier-fixtures/xr7_probe scenarios. An off-path metric wrapper module is not required for scan or publish.


Independent pytest reference math lives in /app/environment/verifier_contracts/xr7_ref_math.py using Python hashlib and struct. Contract tests import xr7_ref_harness and test_xr7_contract.
