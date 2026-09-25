# Platform rubric — bash-cargo-vendor-license-drift-sentinel

**Task folder:** tasks/bash-cargo-vendor-license-drift-sentinel/

Agent implements ingest audit export pipeline with staged manifests under /app/stage/vendor-audit/, +3
Agent parses every Cargo.lock package stanza including duplicate name versions, +3
Agent resolves licenses with license-file before LICENSE and COPYING precedence, +3
Agent computes vendor checksum payloads with trailing newline before sha256, +2
Agent records patch.crates-io lineage and emits patched_crate findings, +2
Agent detects duplicate package name versions across lock stanzas, +2
Agent exports compact sorted JSON with trailing newline and matching CSV rows, +2
Agent refuses export when audit_complete is false on staging manifest, +1
Agent fixes only license precedence while leaving lock parser deduplicating stanzas, -3
Agent patches decoy cargo-metadata-query.sh on the export hot path, -3
Agent re-ingests poisoned vendor trees at export instead of staged audit findings, -5
Agent writes staging manifests outside /app/stage/vendor-audit/, -2
Agent skips hidden tb3 precedence and staging poison workspaces, -2
