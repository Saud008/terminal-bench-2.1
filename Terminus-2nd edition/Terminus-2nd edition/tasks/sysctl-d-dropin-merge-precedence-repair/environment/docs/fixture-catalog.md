# Fixture catalog

| Tree | Focus |
|------|-------|
| `layered-precedence` | Drop-in overrides `main` for the same key |
| `whitespace-sep` | `key value` assignments without `=` |
| `comment-values` | Inline `#` comments and `#` inside values |
| `key-collision` | Ten drop-ins set the same key; seed-keyed `SHA-256("{seed}:{path}")` sort picks processing order and winner |
| `invalid-keys` | Malformed key must fail apply |
| `dropin-invalid` | Invalid key in a drop-in fragment must fail apply with no output |
| `override-stack` | Later fragment overrides one key without dropping others |
| `intra-duplicate` | Duplicate keys within a single fragment; last line wins for value and provenance |
| `error-mid-stack` | Invalid key in a middle drop-in after successful earlier fragments; apply must abort with no output |
| `sparse-main` | Comment-only `main` with assignments only in drop-ins; `stats.files_processed` still counts `main` |
| `cascade-retain` | Four drop-ins each override one key; later fragments must not erase unrelated retained keys |
