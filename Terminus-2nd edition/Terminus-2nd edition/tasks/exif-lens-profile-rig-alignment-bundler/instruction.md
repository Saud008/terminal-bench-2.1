Imaging-lab operators need a host-local photogrammetry rig alignment bundler that keeps EXIF capture staging, lens-profile revision matching, checkerboard calibration gates, rig-slot constraints, missing-frame accounting, and sealed bundle manifests aligned across retries. Operate the rigbundle CLI under /app so ingest, align, and export follow the ops contracts in /app/docs/cli-surface.md, /app/docs/capture-staging.md, /app/docs/exif-timestamp-normalization.md, /app/docs/lens-profile-matching.md, /app/docs/missing-frame-accounting.md, /app/docs/rig-slot-constraints.md, /app/docs/checkerboard-gate.md, and /app/docs/bundle-manifest-export.md.

rigbundle ingest --exif PATH --mount PATH must write /app/state/capture-staging.json and bump /app/state/staging-seq.json. Staging digests and mount inventory binding follow /app/docs/capture-staging.md.

rigbundle align --lenses PATH --checkerboard PATH must advance /app/state/align-generation.json after EXIF timestamp normalization, lens profile revision matching, checkerboard calibration gates, rig slot and allowed-lens validation, and per-slot missing-frame accounting. Captures that fail those gates must appear in /app/output/rejected-captures.jsonl.

rigbundle export must write /app/output/bundle-manifest.json, validate the staged captures digest, and refuse when align_generation is zero. Schema fields and digest binding follow /app/docs/bundle-manifest-export.md.

rigbundle run --exif PATH --mount PATH --lenses PATH --checkerboard PATH executes ingest, align, and export in order.

Binary path: /app/bin/rigbundle. Optional TB3_FIXTURE_DIR overrides the fixture root as documented in /app/docs/cli-surface.md. The wrap decoy helpers under /app/lib/wrap/wrap_decoy.sh are not authoritative for align or export. Do not edit /app/docs/, /app/fixtures/, or /app/config/.
