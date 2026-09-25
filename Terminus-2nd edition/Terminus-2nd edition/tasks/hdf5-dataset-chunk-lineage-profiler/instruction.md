Archive retention engineers run the host-local s5lineage chunk-lineage control plane at `/app/target/release/s5lineage`. Each offline pass walks S5 bundle sidecars—binary S5IX chunk indexes, catalog JSON, and optional per-dataset mask bitsets—then materializes a staging snapshot and, on demand, a compact lineage export for long-term scientific array retention. There is no live object store or remote HDF5 API. This is a data-processing S5 chunk-lineage workflow: keep row-major linear index decoding, parent-chain attribute merge with dataset overrides, catalog-order filter digests, mask-bit tallies per chunk cell span, and scale-derived coordinate labels aligned. It is not a generic audit-report generator, Rust CLI rebuild exercise, cargo toolchain tutorial, or pytest harness task.

Behavior must satisfy the enforceable contracts under `/app/docs/`:

- Catalog fields, dataset paths, and chunk grid dimensions must match `/app/docs/bundle-schema.md`
- S5IX sidecar layout and row-major linear chunk index to origin mapping must match `/app/docs/index-walk.md`
- Parent_chain traversal must apply dataset attribute overrides over inherited keys per `/app/docs/attr-chain.md`
- `filter_chain_hash` must be the SHA-256 of filters joined in catalog order (never sorted) per `/app/docs/filter-chain.md`
- `masked_cells` must count set mask bits only for each chunk cell span per `/app/docs/bit-tally.md`
- `coord_labels` must multiply chunk origin by the effective scale attribute per `/app/docs/origin-labels.md`
- Staging snapshot fields, `export_fingerprint`, byte-stable export, and TB3 overrides must match `/app/docs/report-contract.md`

`s5lineage ingest --catalog DIR --state /app/state` must parse every dataset in the bundle, walk chunk indexes, merge effective attributes, tally mask coverage, and write `/app/state/staging.json`. Each ingest also increments the monotonic counter persisted at `/app/state/sequence.txt` (starting at 1). Every staging chunk record must carry a non-empty `filter_chain_hash`.

`s5lineage export --state /app/state --out /app/output/lineage_report.json` must read the on-disk staging snapshot—not re-derive lineage from raw bundle bytes—and emit lineage report JSON at the caller-provided `--out` path. Export sorts each dataset's chunks ascending by `chunk_index`, binds `export_fingerprint` to the compact JSON encoding of the datasets map only, and must yield byte-identical output when staging is unchanged.

When `TB3_BUNDLE` is set, ingest loads catalog, index, and mask bytes from that directory instead of the `--catalog` path (state paths unchanged). When `TB3_STATE_ROOT` is set, export reads staging from that root instead of `--state`. Hidden verifier bundles live under `/opt/verifier-fixtures/tb3_shadow` unless overridden.

Bundled smoke bundle: `/app/fixtures/basic`. The legacy batch exporter at `/app/src/decoy/legacy_bundle_wrap.rs` is retained for an old migration path and must not participate in ingest or export. Do not edit `/app/docs/`, `/app/fixtures/`, or `/tests/`.
