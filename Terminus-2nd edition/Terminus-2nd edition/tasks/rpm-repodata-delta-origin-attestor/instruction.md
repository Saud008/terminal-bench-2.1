Implement the offline RPM repository delta origin attestor on the working bash baseline under /app. The tool ingests fixture repository trees containing repomd.xml, primary package metadata, modulemd defaults, and mirror snapshot manifests, materializes a normalized staging snapshot at /app/state/repo-stage.json, verifies repodata checksum contracts, ranks NEVRA package lineage per repository, resolves module stream defaults, validates mirror snapshot freshness against repomd revision, and exports a deterministic origin attestation JSON document to /app/output/repo-attestation.json.

Your work must satisfy every contract cited below. The lib/decoy module is not on the ingest or export hot path and must not be edited for a correct export.

The rpm-repo-attest CLI under /app/bin/rpm-repo-attest exposes:

  rpm-repo-attest ingest <repo-dir> --mirror-manifest <path>
  rpm-repo-attest export attestation [--out /app/output/repo-attestation.json]

After ingest, /app/state/repo-stage.json must record the absolute repo directory, mirror manifest path, repomd revision, checksum verification results for primary and modules metadata, normalized package rows with NEVRA keys, module default rows, mirror validation outcome, and a monotonic ingest_seq counter incremented on every ingest call.

export attestation reads staging only and never re-parses repomd.xml or primary.xml from the ingest directory. It writes /app/output/repo-attestation.json using the schema in /app/docs/attestation-export-schema.md.

Repomd data checksum verification must follow /app/docs/repomd-checksum-contract.md: honor the checksum type attribute on each repomd data entry and compare against the on-disk metadata file bytes.

NEVRA lineage ranking must follow /app/docs/nevra-lineage-order.md: epoch participates in the nevra string and lineage_rank uses RPM EVRA ordering within each name and arch group, not plain string sort on version tokens.

Module stream defaults must follow /app/docs/modulemd-default-stream.md: use module_defaults entries from modules.yaml with stream_name and default_profile fields, not alphabetical stream guessing.

Mirror snapshot validation must follow /app/docs/mirror-snapshot-staleness.md: reject stale mirrors when repo_revision lags repomd revision or captured_at predates repomd generation time recorded in the mirror manifest.

Origin digest computation must follow /app/docs/attestation-export-schema.md: sha256 over canonical sorted JSON binding repomd revision, mirror repo_revision, sorted package nevra list, and module default rows.

Bundled fixtures live under /app/fixtures/repos/. Hidden verifier fixtures may supply additional repository trees under /opt/verifier-fixtures/repos/ and TB3_PACKAGE_SALT for per-run package name mutation at runtime. See /app/docs/fixture-catalog.md for bundled repo identifiers.
