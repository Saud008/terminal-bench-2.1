The s6-bundle-resolver under /app/bin reads s6-rc bundle trees and drives mock state transitions, but ingest, validation, ready barriers, apply staging, and graph export for /app/fixtures do not match the contracts under /app/docs/. Repair the broken helpers under /app/lib so the CLI matches those docs. Do not edit /app/docs/ or /app/fixtures/.

Ingest uses /app/tools/bundle_parser.py via /app/lib/ingest.sh. Repair /app/lib/dag.sh so validate, plan, and hard-dep cycle handling match /app/docs/bundle-format.md, /app/docs/dag-contract.md, and /app/docs/cli-reference.md.

Repair /app/lib/ready.sh so longrun ready honors hard parents in rc state per /app/docs/ready-barrier.md. Repair /app/lib/apply.sh so apply writes /app/state/staging.json only after s6-rc change completes, and re-applying the same bundle_id does not duplicate transitions, per /app/docs/staging-apply.md.

Repair /app/lib/export.sh so export includes soft dependencies and accurate edge_count per /app/docs/export-schema.md.

Example: s6-bundle-resolver ingest --tree /app/fixtures/stack --out /app/output/ingest.json

Example: s6-bundle-resolver validate --tree /app/fixtures/cycle --bundle ping-pong

Example: s6-bundle-resolver plan --tree /app/fixtures/stack --bundle web-stack --out /app/output/plan.json

Example: s6-bundle-resolver ready --tree /app/fixtures/stack --bundle web-stack --state-dir /app/state/rc --out /app/output/ready.json

Example: s6-bundle-resolver apply --tree /app/fixtures/stack --bundle web-stack --bundle-id web-stack-v1 --state-dir /app/state/rc

Example: s6-bundle-resolver export --tree /app/fixtures/soft --bundle metrics-edge --out /app/output/graph.json
