# Stage and emit pipeline

## Ingest

```
mdcoll ingest --manifest-dir <DIR> --axes <PATH> --staging /app/state/array_staging.json
```

Ingest reads array manifests, joins axes metadata, validates grid and transforms, fingerprints compressors, and writes a **JSON array** snapshot sorted by `array_name` ascending.

## Export

```
mdcoll export --staging /app/state/array_staging.json --out /app/output/consolidated_manifest.json
```

Emit copies staged rows into `arrays` sorted by `name` ascending.

Totals:

- `expected_chunks` — sum of `expected_chunk_count`
- `missing_chunks` — sum of lengths of `missing_chunk_keys` per array

## Verifier fixture override

When the verifier sets `TB3_MANIFEST_DIR`, stage must read manifests from that directory. Axes default to `/app/environment/fixtures/axes.json` unless `TB3_AXES_PATH` is set.

Bundled hidden manifests for grading live at `/opt/verifier-fixtures/zarr_hidden/manifests`. Alternate axes catalog for grading lives at `/opt/verifier-fixtures/zarr_hidden/axes_alt.json`.

The release build installs the consolidator binary at `/app/bin/mdcoll`.
