# Platform rubric — rust-webbundle-integrity-section-verifier

**Task folder:** tasks/rust-webbundle-integrity-section-verifier/

Agent parses WBLE bundle headers with little-endian exchange counts from binary archives, +3
Agent canonicalizes URLs with lowercase host and path segment normalization, +3
Agent applies scope prefix boundary rules when matching exchange URLs, +3
Agent validates integrity section digests using canonical URL status and header preimage, +3
Agent resolves duplicate exchanges by highest variant_id after canonicalization, +2
Agent strips Content-Type charset parameters before MIME allow-list checks, +2
Agent writes exchange_attestation.jsonl sorted by canonical_url ascending during scan, +2
Agent exports bundle_attestation_report.json with separate scope and hash violation totals, +2
Agent honors TB3_BUNDLE_DIR override for alternate bundle directories, +2
Agent produces scan and attestation report output through wbleguard CLI subprocesses, +2
Agent patches decoy_audit crate expecting attestation report output changes, -3
Agent hardcodes bundle_attestation_report.json without running wbleguard emit-attestation, -5
Agent fixes URL canonicalization only while leaving integrity hash preimage broken, -3
Agent counts scope_violations as zero in export totals despite out-of-scope rows, -3
Agent reads bundled fixtures when TB3_BUNDLE_DIR points elsewhere, -3
