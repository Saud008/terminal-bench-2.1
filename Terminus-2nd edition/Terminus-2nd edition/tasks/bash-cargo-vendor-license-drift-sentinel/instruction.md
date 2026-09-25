Task identity cvls8f2a91 defines the SPDX supply-chain compliance sentinel for vendored Cargo trees. See /app/docs/engineering-problem-contract.md for contracts.

Implement the cvls-governor compliance governor on the working baseline under /app. The CLI at /app/scripts/cvls-governor must accept a workspace path containing Cargo.lock, Cargo.toml, lock-metadata.json, and vendored crates, then produce the SPDX-oriented staging and export artifacts defined in /app/docs/. Cite /app/docs/cli-surface.md, /app/docs/lock-parsing.md, /app/docs/spdx-precedence.md, /app/docs/vendor-checksum.md, /app/docs/patch-lineage.md, /app/docs/spdx-glossary.md, /app/docs/staging-format.md, /app/docs/export-format.md, and /app/docs/fixture-catalog.md.

For --workspace PATH, staging is /app/stage/license-compliance/WORKSPACE_BASENAME.json where WORKSPACE_BASENAME is the final directory name. Example: --workspace /app/fixtures/workspaces/baseline writes /app/stage/license-compliance/baseline.json. publish refuses until attest set audit_complete.

Worked example outputs: /app/output/vendor-compliance.json and /app/output/vendor-compliance.csv.

The lock parsing contract is defined in /app/docs/lock-parsing.md. Inventory outputs must preserve every package entry needed for the later attest and publish stages.

License drift findings must use the precedence and normalization rules in /app/docs/spdx-precedence.md.

Checksum mismatch findings must follow the checksum contract in /app/docs/vendor-checksum.md.

Patched crate findings must follow the lineage contract in /app/docs/patch-lineage.md.

Duplicate package names with multiple versions must emit duplicate_versions findings in the export format documented in /app/docs/export-format.md.

Inventory must write the staging artifact described in /app/docs/staging-format.md. Attest is valid only after ingest_complete and must record findings plus audit_digest on that staged artifact. Publish is valid only after audit_complete and must emit the deterministic JSON and CSV outputs described in /app/docs/export-format.md from staged audit data.

The decoy at /app/decoy/cargo-metadata-query.sh is diagnostic only and not on the publish hot path.
