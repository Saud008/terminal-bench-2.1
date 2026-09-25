# Signed-exchange bundle attestation lab

Implement wbleguard on the working Rust tree at /app/environment: an attestation checker for signed HTTP exchanges packaged as WBLE archives. The tool catalogs on-disk bundle fixtures into JSONL exchange records at /app/state/exchange_attestation.jsonl, then emits a structured attestation dossier at /app/output/bundle_attestation_report.json that records IHSH integrity failures, signed-exchange scope boundary violations, and MIME allow-list breaches.

Complete wbleguard so catalog-bundles and emit-attestation follow /app/docs/scope_and_integrity.md. Required behaviors include signed-exchange URL normalization (lowercase host, path decoding rules in /app/docs/url_canonicalization.md), IHSH integrity section validation against response headers and bodies, duplicate exchange resolution by highest exchange variant identifier, prefix scope rules with path boundaries, MIME allow-list checks ignoring charset parameters, and attestation export with accurate violation counters.

## Operator workflow

1. Rebuild release wbleguard via /app/environment/scripts/build_all.sh.
2. Catalog bundled WBLE fixtures into /app/state/exchange_attestation.jsonl.
3. Emit attestation evidence to /app/output/bundle_attestation_report.json.

## Authoritative contracts

Study these product specs (not this page alone):

- /app/docs/wble_format.md — binary WBLE container layout
- /app/docs/url_canonicalization.md — signed-exchange URL normalization
- /app/docs/scope_and_integrity.md — IHSH digests, scope boundaries, TB3_BUNDLE_DIR override
- /app/docs/evidence_report.md — report schema and totals semantics

Evidence output must list bundles by bundle_id, order exchanges by normalized URL, emit finding kinds hash_mismatch / scope_violation / ctype_violation, and keep verified_count aligned with staged rows.

Grading invokes wbleguard through subprocess after cargo rebuild; hardcoding report JSON fails hidden bundle scenarios under /opt/verifier-fixtures/wble_hidden/bundles documented in /app/docs/scope_and_integrity.md.
