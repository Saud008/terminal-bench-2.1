# Runtime paths for wantplay

Session driver config at /app/config/want-session.json defines idle_limit_ms and default staging paths used by the traceplay/orchestrator stack.

Pipeline exports use caller-chosen --output paths. Bundled examples and pytest use /app/output/session-report.json and /app/output/metrics-report.json per /app/docs/exchange-contract.md.

Staging snapshot path defaults to /app/state/want-snapshot.json.
