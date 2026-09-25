# CLI surface

The cvls-governor driver at /app/scripts/cvls-governor exposes inventory, attest, and publish stages.

## inventory

```
cvls-governor inventory --workspace <path>
```

Reads Cargo.lock, lock-metadata.json, vendor/, and Cargo.toml patch tables. Writes staging manifest to /app/stage/license-compliance/WORKSPACE_BASENAME.json where WORKSPACE_BASENAME is the final directory name of the workspace path.

The staging file contains packages[], workspace_fingerprint, patch_map, and ingest_complete=true.

inventory exits 2 when --workspace is missing, unknown flags are passed, or the workspace path is not a directory.

## attest

```
cvls-governor attest --workspace <path>
```

Requires ingest_complete on the staging manifest. Computes license drift, checksum mismatches, patched crate lineage, and duplicate package name versions. Sets audit_complete=true and findings[].

attest exits 2 when --workspace is missing, unknown flags are passed, the workspace path is not a directory, or the staging manifest is missing.

## publish

```
cvls-governor publish --workspace <path> --json <path> --csv <path>
```

Requires audit_complete. Writes deterministic JSON report and CSV findings table per export-format.md. publish exits 2 when required flags are missing or unknown flags are passed. It refuses when the audit block is missing (exit 3).

Publish must emit findings from the staged audit block only and must not re-walk the workspace vendor tree.
