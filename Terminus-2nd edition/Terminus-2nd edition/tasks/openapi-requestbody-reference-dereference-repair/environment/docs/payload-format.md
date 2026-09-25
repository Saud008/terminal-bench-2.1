# Payload fixture format

Each file under `/app/fixtures/payloads/` is JSON:

```json
{"operation":"POST /pets","data":{"petType":"cat","name":"mittens"}}
```

- `operation` — target operation for schema lookup.
- `data` — request body object to validate.
