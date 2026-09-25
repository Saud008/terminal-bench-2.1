# Wireclock response schema

## POST /v1/mint

Request: `{ "now_unix": int, "machine_id": string, "count": int }`
Response: `{ "ids": [string, ...] }` — each id is 24 lowercase hex characters.

## POST /v1/wire-doc

Request: `{ "_id": string, "payload": object }`
Response: `{ "bson_b64": string }`

## POST /v1/admit

Headers: `X-Test-Now` (int seconds), `X-Machine-Id` (string)
Request: `{ "documents": [ { "client_seq": int, "payload": object }, ... ] }`
Response: `{ "results": [ { "_id": string, "client_seq": int, "repeat_claim": bool }, ... ] }`

State written: `/app/state/digestseal-batch.json` with fields `machine_id`, `now_unix`, `batch_digest`, `documents`.

## POST /v1/resume

Request: `{ "resume_path": string }` — absolute path to JSONL under `/app/work/jsonl-resume`
Response: `{ "applied": int }` — count of lines newly persisted during this request only.

State written: `/app/state/srcursor-by-path.json` maps each resume path to applied line numbers.

## GET /v1/stats

Response: `{ "documents": int, "resume_lines": int }`

Persistence database: `/app/data/oidguard.db`
