# Fixture catalog

Bundled under /app/fixtures/exchange/:

001-basic-wants.jsonl — baseline want and delivery trace.

002-alias-merge.jsonl — merge_wants with alias CID strings.

003-cancel-inflight.jsonl — cancel ordering trace.

004-ledger-dedupe.jsonl — peer ledger credit trace.

005-idle-partial.jsonl — session idle tick trace.

006-priority-cancel.jsonl — metrics queue head trace.

007-pipeline-mixed.jsonl — combined pipeline regression trace.

Held-out verifier traces are not baked into the agent image. They are supplied only at grade time under /tests/hidden/exchange/ (or an absolute TB3_FIXTURES_DIR overlay).
