# Idempotent export

Report JSON ends with a trailing newline.

A second emit-diff without state mutation must produce byte-identical xds-diff-report.json.
