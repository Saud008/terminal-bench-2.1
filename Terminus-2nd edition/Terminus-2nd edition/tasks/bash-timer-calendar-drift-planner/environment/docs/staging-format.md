# Staging format

Manifest path: /app/stage/manifests/BUNDLE_BASENAME.json

After load:

- ingest.timer_name
- merged_timer object with merged Timer keys

After forecast:

- forecast object with drift fields defined in export-format.md

write-report requires the forecast block.
