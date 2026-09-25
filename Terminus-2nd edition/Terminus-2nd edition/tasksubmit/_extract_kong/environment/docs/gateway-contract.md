# Gateway contract

The `kongadmit` security control plane at `/usr/local/bin/kongadmit` exposes:

- **Proxy** on `proxy_listen` from `/app/config/gateway.json` (default `127.0.0.1:8000`)
- **Admin** on `admin_listen` (default `127.0.0.1:8001`)

Admin endpoints:

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness |
| POST | `/admin/ingest` | Load declarative deck (`{"deck_path":"/path/to/deck.yaml"}`) |
| POST | `/admin/reload` | Reload deck from configured `deck_path` |
| GET | `/admin/export/openapi` | Export staged OpenAPI 3.0 document |
| POST | `/admin/reset-rates` | Clear in-memory rate counters |

On startup, `serve` loads the configured `deck_path` when present. A subsequent failed `/admin/ingest` must still follow atomic ingest rules in `/app/docs/declarative-ingest.md` (clear all routes, `routes_loaded` 0 on 422).

Leave `/usr/local/bin/kongadmit` current after source edits (the verifier may invoke `/app/scripts/verifier-rebuild.sh`). Start with:

```bash
kongadmit serve --config /app/config/gateway.json
```

Allowed plugins: `jwt`, `rate-limiting`, `response-transformer`.
