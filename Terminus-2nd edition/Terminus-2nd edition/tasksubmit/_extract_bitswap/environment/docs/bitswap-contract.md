# Bitswap contract

On this system-administration host-local bitswap session control plane, bswapd admits JSONL traces that model wantlist exchange without network I/O. Each trace line is one event with monotonic seq.

Pipeline command:

bswapd pipeline --log PATH --session NAME --output /app/output/session-report.json

Metrics command:

bswapd metrics --log PATH --session NAME --output /app/output/metrics-report.json

The --output path is caller-chosen; bundled examples and pytest use /app/output/session-report.json for pipeline exports and /app/output/metrics-report.json for metrics exports.

Ingest applies events to an in-memory session, writes /app/state/bitswap-snapshot.json, then export reads that snapshot only. Export must not re-walk trace files or read scratch manifests for wants_remaining.

Display versus canonical CID rules for every output row are in /app/docs/bitswap-display-cid-rules.md. Staging and export field shapes are in /app/docs/bitswap-staging-snapshot.md and /app/docs/bitswap-session-export.md.

Canonical multihash keys come from /app/docs/bitswap-display-cid-rules.md. Cancel and in-flight rules are in /app/docs/bitswap-cancel-inflight-guard.md. Idle cleanup is in /app/docs/bitswap-session-idle-limits.md.

Optional TB3_SESSION_PREFIX and TB3_FIXTURES_DIR override session naming and hidden fixture roots when set to absolute paths. Optional VERIFIER_SEED overrides the default pytest session hash seed when set to a non-empty string.
