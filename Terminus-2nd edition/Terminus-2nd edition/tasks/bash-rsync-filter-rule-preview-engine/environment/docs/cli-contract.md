# CLI contract

ingest requires --tree and --run-id and writes /app/work/<run-id>-inventory.json.
Example inventory path: /app/work/run-inv-inventory.json when run-id is run-inv.
compile requires --run-id and reads inventory output then writes /app/state/filter-compiled.json.
export requires --run-id and --output; when output is omitted by caller wrappers, default is /app/output/rsync_filter_preview_atlas.json.
Example export run-id values include run-export-stage for atlas emission checks.

Bundled tree manifests live at /app/fixtures/trees/media-sync/manifest.json, /app/fixtures/trees/receiver-drift/manifest.json, and /app/fixtures/trees/docs-cascade/manifest.json.
Sample probe paths include cache/tmp.bin, albums/live/set1.flac, and configs/legacy.yml from those manifests.
Additional evaluation tree roots may appear under /opt/verifier-fixtures/rsyncprev/trees.
