# Fixture catalog

Sources live under `/app/fixtures/sources/`. Batches under `/app/fixtures/batches/` describe RPC sequences (open → change → close/export).

| File | Notes |
|------|-------|
| `ascii-base.dlint` | ASCII-only baseline |
| `emoji-prefix.dlint` | Leading emoji surrogate pair |
| `wide-mix.dlint` | Mixed BMP + supplementary characters |
| `paren-todo.dlint` | TODO markers and unbalanced parens |

Seeds in `/app/fixtures/seeds.json` mutate edit payloads during batch replay — do not hardcode batch text in client drivers.
