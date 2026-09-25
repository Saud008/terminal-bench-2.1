Implement the packctl git packfile delta-chain resolver and object export governor on the working Rust baseline under /app. The tool ingests pack bundle directories containing catalog.json and pack.stream bytes, materializes an on-disk object adjacency staging snapshot at /app/state/pack-stage.json, resolves OFS_DELTA and REF_DELTA chains into inflated object payloads per pack contracts, and exports per-object inflated sizes and SHA-1 identities to /app/output/pack-object-export.json with a pack-level total_inflated_bytes rollup.

Your work must satisfy every contract cited below. The src/decoy module is not on the ingest or resolve export hot path and must not be edited for a correct export.

Build /app/bin/packctl from the workspace root. Subcommands:

  packctl ingest <pack-dir>
  packctl resolve export

After ingest, /app/state/pack-stage.json must list pack entries in catalog order with object id, kind, pack_offset, base links, and ingest metadata copied from catalog.json.

resolve export reads staging only (never re-parse catalog.json from the ingest directory). It writes /app/output/pack-object-export.json using the schema in /app/docs/pack-export-schema.md. Chain resolution must follow /app/docs/delta-chain-ordering.md: inflate bases before dependents using longest-base-first topological ordering, not depth-first leaf-first walks.

OFS_DELTA base windows must follow /app/docs/ofs-delta-window.md: copy offsets are measured from the pre-image base window start in the resolved base bytes, not from the post-patch cursor.

REF_DELTA base selection must follow /app/docs/ref-delta-kind-gate.md: validate the base object kind is an allowed delta base before loading base bytes from the staging graph.

Zlib inflate for chained objects must follow /app/docs/zlib-chain-isolation.md: each chain link gets a fresh inflate output buffer; reusing one buffer across links corrupts patched bytes.

Export byte rollup must follow /app/docs/export-size-rollup.md: total_inflated_bytes sums final inflated payload lengths only, not intermediate delta compressed sizes.

Bundled fixtures use the /app/data/packs/shallow directory. Hidden verifier fixtures may supply additional pack bundles under /opt/verifier-fixtures/pack-bundles and TB3_OBJECT_ID_SALT for per-run object id mutation at runtime.
