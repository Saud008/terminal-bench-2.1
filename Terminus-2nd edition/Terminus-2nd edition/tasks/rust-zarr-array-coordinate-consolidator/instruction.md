Task identity d8a09f1c42 defines the engineering problem for rust zarr array coordinate consolidator. See /app/docs/engineering-problem-contract.md for root cause and failure mode contracts.

# Zarr array metadata consolidator

Build the array metadata consolidator for the climate archive lab under /app. The tool stages array metadata from manifest bundles and coordinate axes, then writes a consolidated manifest for downstream catalog services. Grading checks spatial coordinate invariants, canonical ascending ordering of array rows, deterministic idempotent export bytes, and topology closure for absent shard keys.

Use the ingest and export subcommands documented in /app/docs/staging_export_pipeline.md. Ingest validates array topology, coordinate transform consistency, absent key accounting, and compressor fingerprints.

## Workflow

1. Rebuild with /app/environment/scripts/build_all.sh.
2. Ingest bundled manifests to /app/state/array_staging.json (verified by tests).
3. Export /app/output/consolidated_manifest.json (verified by tests).

## Contracts

- /app/docs/array_manifest_format.md
- /app/docs/chunk_grid_rules.md
- /app/docs/coordinate_transforms.md
- /app/docs/compressor_fingerprint.md
- /app/docs/staging_export_pipeline.md (TB3_MANIFEST_DIR override)

Grading invokes the consolidator CLI via subprocess after rebuild; hardcoded outputs are insufficient. Verifier reference math lives at /app/environment/verifier_contracts/zarr_refmath.py.
