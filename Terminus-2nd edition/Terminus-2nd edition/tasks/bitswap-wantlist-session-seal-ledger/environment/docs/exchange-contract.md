# Exchange contract

On this swarm-trade wantlist arena playfield, wantplay admits JSONL scenario packs that model wantlist exchange without network I/O. Each trace line is one event with monotonic seq.

Pipeline command:

wantplay pipeline --log PATH --session NAME --output /app/output/session-report.json

Metrics command:

wantplay metrics --log PATH --session NAME --output /app/output/metrics-report.json

The --output path is caller-chosen; sealed JSON must land only at that path. Bundled examples use /app/output/session-report.json for pipeline and /app/output/metrics-report.json for metrics. Verifier runs may pass dynamic paths such as /app/output/export-{suffix}.json and /app/output/metrics-{suffix}.json.

session_id in staging and every export must equal the exact --session NAME string. Callers may pass dynamic names. When TB3_SESSION_PREFIX and VERIFIER_SEED are present, dynamic names follow `{TB3_SESSION_PREFIX}-{sha256("{VERIFIER_SEED}:{suffix}") hex[:8]}` with defaults TB3_SESSION_PREFIX=tb3 and VERIFIER_SEED=bitswap-wantlist-session-seal-ledger.

Ingest applies events to an in-memory session, writes /app/state/want-snapshot.json, then export reads that snapshot only. Export must not re-walk trace files or read scratch manifests for wants_remaining.

Display versus canonical token rules for every output row are in /app/docs/exchange-display-token-rules.md. Staging and export field shapes are in /app/docs/exchange-staging-snapshot.md and /app/docs/exchange-session-export.md.

Canonical multihash keys come from /app/docs/exchange-display-token-rules.md. Cancel and in-flight rules are in /app/docs/exchange-cancel-inflight-guard.md. Idle cleanup is in /app/docs/exchange-session-idle-limits.md.

Optional TB3_SESSION_PREFIX and TB3_FIXTURES_DIR override session naming prefix and held-out fixture roots when set. Optional VERIFIER_SEED overrides the default session hash seed when set to a non-empty string. Held-out traces are not present in the agent runtime image; they are supplied only at verifier grade time under /tests/hidden/exchange/ (or TB3_FIXTURES_DIR).
