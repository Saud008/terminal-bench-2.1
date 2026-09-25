# Track event format

Events are JSONL under /app/fixtures/events/ or verifier-only paths.

Each line:

```json
{
  "event_id": "<unique string>",
  "ts": <integer epoch seconds>,
  "track": "<track name from config>",
  "status": "ok" | "fail",
  "exit_code": <integer>
}
```

Events are processed in file order. The same event_id must not change state twice on replay.

Track names must exist in /app/config/vrrp.json tracks array.
