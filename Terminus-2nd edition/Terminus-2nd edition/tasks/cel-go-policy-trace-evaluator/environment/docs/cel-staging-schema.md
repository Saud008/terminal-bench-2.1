# CEL staging snapshot schema

celctl ingest writes `/app/state/cel-staging.json` with this shape:

| Field | Type | Meaning |
|-------|------|---------|
| version | integer | Always 1 |
| source | string | Absolute path of input AST JSON |
| ast_hash | string | Lowercase hex SHA-256 of canonical input bytes |
| normalized | object | Parsed AST root node |

The normalized object uses node kinds documented in `/app/docs/cel-eval-semantics.md`. Ingest must not evaluate expressions. Export and eval stages read only the staging file, not the original input path.

Re-ingesting the same input with an unchanged AST must produce identical ast_hash and normalized content.
