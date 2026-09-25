# Export report schema

export writes UTF-8 JSON:

```json
{
  "scenario": "clean-pipeline",
  "audit_generation": 1,
  "unsafe_count": 0,
  "findings": [],
  "audit_digest": "...",
  "safe_for_resume": true
}
```

- audit_generation must equal both staging audit_generation and /app/state/audit-generation.json audit_generation.
- findings copied from audit-findings.json in sorted order (task_id then rule). Each finding object has keys task_id, rule, detail with the detail strings defined in unsafe-cache-rules.md.
- audit_digest is the lowercase hex SHA-256 of the findings array serialized as compact JSON: `json.dumps(findings, separators=(",", ":"))` with object key order task_id, rule, detail and no extra whitespace.
- safe_for_resume is true only when unsafe_count is zero.
- export must fail when audit has not run (audit_generation zero or generation file missing).
- export reads staging and the generation latch only; it does not accept or require --fixture-dir.
