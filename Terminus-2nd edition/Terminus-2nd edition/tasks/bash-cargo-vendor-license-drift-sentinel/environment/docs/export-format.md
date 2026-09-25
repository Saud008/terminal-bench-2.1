# Export format

JSON reports use schema_version as the string "1" and include workspace_id, workspace_fingerprint, run_seq, audit_digest, summary, findings, and packages.

summary counts license_drift, checksum_mismatch, patched_crate, and duplicate_versions findings.

Each finding kind has an exact JSON shape:

- license_drift includes kind, package, version, declared, and resolved.
- checksum_mismatch includes kind, package, version, expected, and computed.
- patched_crate includes kind, package, version, patch_path, and registry_fallback. The finding does not carry source_kind.
- duplicate_versions includes kind, package, and versions. The finding does not carry a version field.

packages rows keep declared_license, resolved_license, checksum_mismatch, and patch_lineage. patch_lineage carries patch_path, source_kind, and registry_fallback when the package came from [patch.crates-io].

JSON serialization uses sort_keys true, separators comma colon without spaces, and a single trailing newline.

CSV columns are kind, package, version, declared_license, resolved_license, and detail. One row is emitted per finding. license_drift rows copy declared and resolved into the declared_license and resolved_license columns. checksum_mismatch rows put computed in detail. patched_crate rows put patch_path in detail. duplicate_versions rows leave version empty and put pipe-joined versions in detail.
