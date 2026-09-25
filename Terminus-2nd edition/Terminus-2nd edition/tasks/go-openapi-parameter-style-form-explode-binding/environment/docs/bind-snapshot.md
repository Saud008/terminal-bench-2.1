# Bind snapshot staging

After policy evaluation succeeds, paramgate must seal the canonical bound values into a witness snapshot before returning HTTP **200**.

## Snapshot file

Path: `/app/state/bind-snapshot.json`

The `/app/state/` directory must exist before writing; `/app/scripts/reset-state.sh` recreates it and clears only the snapshot file between verifier cases.

Written on every successful bind. Shape:

```json
{
  "bind_seq": 1,
  "method": "GET",
  "route": "/v1/catalog/items",
  "params": { "...": "..." },
  "body": { "...": "..." }
}
```

`body` is omitted when the operation has no request body. `bind_seq` starts at **1** and increments by **1** on each successful bind (monotonic for the process lifetime).

## Response emission

The HTTP handler must build the **200** JSON payload from the staged snapshot (`params` and optional `body`), not from transient in-memory maps left over from parsing. If the snapshot is missing or unreadable, treat it as an internal fault (**500**).

Binding parsers under `/app/internal/bind/` populate the in-memory result; canonicalization orders nested object fields per `/app/docs/canonical-bind-order.md`; staging persists that result; the export publisher in `/app/internal/bind/publish.go` reads the snapshot back for the API response (via `EmitSuccess`). See also `/app/docs/param-binding-contract.md` and `/app/docs/bind-api.md`.
