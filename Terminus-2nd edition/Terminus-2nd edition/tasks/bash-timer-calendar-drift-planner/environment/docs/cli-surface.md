# timdrift CLI surface

Driver: /app/scripts/systemd-timer-planner.sh (also on PATH as systemd-timer-planner)

Subcommands:

- load --bundle PATH --timer-name NAME
- forecast --bundle PATH --context PATH --now ISO8601_Z
- write-report --bundle PATH --out PATH

Manifest path: /app/stage/manifests/BUNDLE_BASENAME.json

write-report refuses when forecast block is missing from manifest.

Default context: /app/context/default.json

Example export: /app/output/drift-report.json
