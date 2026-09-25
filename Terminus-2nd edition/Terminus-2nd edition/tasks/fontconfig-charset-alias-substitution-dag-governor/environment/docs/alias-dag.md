# Alias DAG contract

`<alias from="A" to="B"/>` declares a directed edge **A → B**. Alias names are opaque strings.

## Expansion

Given a starting alias name (from a charset `<alias ref="…"/>` or a direct query), walk edges until:

1. **Terminal charset** — the name matches a `<charset name="…">` entry (full name, not short).
2. **Unknown name** — no edge and no charset → error.

Follow the full chain: `A → B → C → terminal`. One-hop lookup is insufficient.

## Cycle detection

If expansion re-enters a name on the active path, the configuration contains an **alias cycle**. The `check` subcommand must exit **2** and print `alias cycle detected` to stderr.

Cycle detection runs over the merged alias graph after config + inject overlay are combined. Self-loops count as cycles.

## Encoding propagation

Each charset may declare `encoding="…"`. When alias expansion terminates on charset **T**, the resolved encoding is **T.encoding**, even when the query started from a different charset node in the chain.

Example: query charset `ISO8859-1:1987` with alias ref `latin-core` → `unicode-bmp`, where `unicode-bmp` declares `encoding="utf-8"`. Resolved encoding is `utf-8`, not the query charset's local encoding.

## Merge semantics

Config and inject fragments merge by **appending** elements in file order. Later alias edges replace earlier edges with the same `from` key. Charset entries are keyed by **`name` (full)** — never by `short` alone.
