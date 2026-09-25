# Trust surface

Binary: `/usr/local/bin/livattest`
Config: `/app/config/livattest.json`
Listen: `:8080` by default
Database: `/app/work/livattest.db`
Witness snapshot: `/app/state/witness-snapshot.json`
Attest report: `/app/output/attest-report.json`
State reset helper: `/app/scripts/reset-state.sh`
Binary rebuild helper: `/app/scripts/verifier-rebuild.sh`

Report field schema: `/app/docs/attest-report-format.md`
Witness staging schema: `/app/docs/witness-chain.md`

## Routes

| Method | Path | Role |
|--------|------|------|
| GET | `/health` | Liveness probe |
| POST | `/v1/trust/bind` | Bind token+session, mint admission ticket |
| POST | `/v1/attest/batch` | Admit attest beats under ticket + continuity policy |
| POST | `/v1/attest/export` | Publish digest-sealed attest report |

Header `X-Test-Mono-Ms` pins monotonic milliseconds for the request.

## Bind body

```json
{"token":"...","session_id":"...","client_ms":0}
```

Response includes `admission_ticket` (hex HMAC). Missing `token` or `session_id` → HTTP 400.

## Batch body

```json
{"token":"...","session_id":"...","admission_ticket":"...","beats":[{"seq":1,"client_ms":0}]}
```

Missing required fields, unbound session, or bad/missing ticket → HTTP 400.
Duplicate accepted seq or skew violation → HTTP 409.

## Export body

```json
{"token":"...","session_id":"..."}
```
