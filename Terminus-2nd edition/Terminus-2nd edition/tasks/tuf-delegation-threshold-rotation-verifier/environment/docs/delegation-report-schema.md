# Delegation report schema

export report writes delegation-report.json with:

- epoch: verification epoch integer
- rotation_ok: boolean from verify-result
- decisions: array sorted by path ascending. Each row has path, allowed boolean, delegation string or null, reason string
- audit_digest: lowercase hex SHA-256 of the canonical JSON encoding of the decisions array only

rejected-targets.jsonl contains one JSON object per line for decisions where allowed is false. Lines follow decisions sort order. Each object includes path, reason, and delegation (string or null).

Allowed targets omit from rejected-targets.jsonl.
