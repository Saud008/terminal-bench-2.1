# Compile and staging workflow

fc-alias-check uses a two-stage pipeline. **ingest** parses fontconfig XML, merges optional inject fragments, and writes a normalized staging snapshot. **resolve** reads staging only and must never re-parse XML from the original config paths.

## ingest

```text
fc-alias-check ingest \
  --config /app/fixtures/configs/<file>.conf \
  [--inject /path/to/fragment.conf]
```

Writes `/app/state/fc-compiled.json` and bumps `/app/state/compile-seq.txt`.

Exit **0** on success.

## resolve

```text
fc-alias-check resolve \
  --charset <full-charset-name> \
  --family <family-query> \
  --export /app/output/<report>.json
```

Reads `/app/state/fc-compiled.json` only. Exit **1** with `compiled staging missing; run ingest first` when staging is absent.

## check

```text
fc-alias-check check \
  --config /app/fixtures/configs/<file>.conf \
  [--inject /path/to/fragment.conf]
```

Exit **0** when no alias cycle exists. Exit **2** when a cycle is detected (stderr contains `alias cycle detected`).

## Build note

The workspace image ships `/usr/local/bin/fc-alias-check` prebuilt. Rebuild with `CARGO_NET_OFFLINE=true cargo build --locked --release -p fc-alias-check` after Rust edits. Do not run `cargo install` during verification.

## Export JSON schema

```json
{
  "schema": "fc-alias-check/1",
  "charset_query": "<requested name>",
  "family_query": "<requested family>",
  "charset": {
    "name": "<full name>",
    "short": "<short>",
    "encoding": "<local encoding>",
    "alias_ref": "<first alias hop>"
  },
  "alias_chain": ["<hop>", "..."],
  "resolved_terminal": "<terminal charset name>",
  "encoding": "<propagated encoding from terminal>",
  "substitute": {
    "family": "<family>",
    "preferred": ["<family>", "..."]
  },
  "reject_bitmap": false,
  "reject_outline": false,
  "font_kinds_allowed": ["bitmap", "outline"],
  "compile_meta": {
    "compile_seq": 1,
    "graph_hash": "<hex digest>"
  }
}
```

`alias_chain` lists intermediate alias hops only, in walk order, **excluding** both the query charset name and the terminal charset name. The terminal charset appears solely in `resolved_terminal`.

## Inject overlay

`--inject` on **ingest** loads an additional fragment merged after the base config. Used by tests for ephemeral alias and charset overrides without editing fixture trees.
