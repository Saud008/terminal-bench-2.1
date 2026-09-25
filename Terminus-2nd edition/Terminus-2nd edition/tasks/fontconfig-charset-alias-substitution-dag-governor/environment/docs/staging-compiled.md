# Staging compiled snapshot

Path: `/app/state/fc-compiled.json`

Schema: `fc-compiled/1`

## Fields

| Field | Meaning |
|-------|---------|
| `schema` | Always `fc-compiled/1` |
| `compile_meta.compile_seq` | Monotonic counter from `/app/state/compile-seq.txt` |
| `compile_meta.graph_hash` | djb2 16-digit lowercase hex digest of merged config canonical form plus inject path |
| `config_path` | Absolute path of base config used at compile |
| `inject_path` | Absolute inject path when present, else JSON null |
| `config` | Merged fontconfig model after parse |

## Charset order

Charset rows in `config.charsets` must preserve **source declaration order** from the merged XML. Reordering, reversing, or collapsing by `short` before staging breaks revision-specific fixtures.

## graph_hash

Compute a 16-digit lowercase hex digest using djb2 over UTF-8 bytes of:

```text
<base-path>\n<inject-path-or-empty>\n<canonical-json>
```

`canonical-json` is serde JSON of the merged `config` with charset list in declaration order, alias pairs in parse order, and both reject flags included.

Hashing only the base config path string, or omitting inject path content, produces incorrect digests when inject overlays change alias or charset data.

## compile_seq

Each successful `ingest` increments the counter persisted at `/app/state/compile-seq.txt`. Re-running ingest on unchanged inputs still bumps the counter. Resolve exports echo the `compile_meta` copied from the staging file read at resolve time.

## Resolve contract

`resolve` must load staging from disk and must not call `load_merged` or re-read XML from `config_path` / `inject_path`. Export `compile_meta` must match the staging snapshot used for that resolve call.

The `src/decoy` module provides label normalization helpers that are **not** on the compile or resolve hot path.
