# Bundle verification contract

Rules for `bundlectl verify`.

## Command

```text
bundlectl verify --bundle <dir>
```

`verify` does **not** accept `--seed`. It hashes on-disk bundle bytes only (placeholders such as `__THRESHOLD__` in fixture input files are never substituted during verify).

## Bundle layout

Each bundle directory contains:

| Path | Role |
|------|------|
| `MANIFEST.json` | Lists `members` (relative paths) and `roots` |
| `.signatures.json` | Scoped signature entries |
| `data/data.json` | Document tree for `data.*` references |
| `policies/*.rego` | Rego modules |
| `trust/revoked-keys.json` | Revoked `key_id` values |

`MANIFEST.json` and `.signatures.json` are **not** members of the digest chain.

## Path canonicalization

Before sorting or hashing, canonicalize every member path:

1. Replace backslashes with `/`.
2. Remove a leading `./`.
3. Collapse `/./` and resolve `..` segments (POSIX-style).
4. Reject paths that escape the bundle root after canonicalization.

Module import paths in policies use dotted form (`policy.main`); file paths use slash form (`policies/allow.rego`).

## Member digest chain (full bundle)

Let `M` be manifest `members` minus `MANIFEST.json` and `.signatures.json`, each path canonicalized.

Sort `M` by **UTF-8 lexicographic order** of canonical paths (not manifest declaration order).

```
state = SHA256("")   # 32-byte digest of the empty string
for path in sorted(M):
  state = SHA256(state || path || SHA256(file_bytes))
chain_root = hex(state)
```

## Scoped signatures

Each entry in `.signatures.json`:

```json
{"key_id": "...", "scope": "policies/", "chain_root": "<hex>"}
```

For scope `S`, take members in `M` whose canonical path has prefix `S`, sort lexicographically, and compute the same rolling digest **only over that subset**. `chain_root` must equal the scoped result.

Verify Ed25519-style signatures only after chain roots match: `signature = HMAC-SHA256(key_material, scope || chain_root)` compared as hex (keys in `/app/trust/keys.json`).

## Revoked keys

If `key_id` appears in `trust/revoked-keys.json`, verification must fail with non-zero exit and `"revoked": true` in JSON output.

## Seed substitution (evaluation only)

Only `bundlectl eval` performs seed substitution. Apply it to the `--input` JSON bytes **before** parsing JSON.

Input templates store the placeholder inside a JSON **string** value, for example:

```json
{"threshold": "__THRESHOLD__"}
```

Replace the literal token `__THRESHOLD__` with the decimal digits of `tag` (text substitution only — keep the surrounding JSON quotes so the field stays a string):

```text
digest = SHA256("<build-seed>:<seed>")   # 32 raw bytes, not hex
tag = (int(digest[0]) << 8 | int(digest[1])) % 900 + 100
```

After substitution the parsed input is `{"threshold": "204"}` (JSON string `"204"`), not a numeric `204`. Trace bindings must export the substituted JSON value with the same type.

Build seed is fixed in `/app/internal/seed/seed.go`.

## Verify output

On success, stdout JSON includes `"ok": true`, `"chain_root"`, and `"digests"` as a JSON **object** whose keys are canonical member paths and whose values are per-file SHA-256 hex digests (for example `"digests": {"data/data.json": "<hex>", "policies/allow.rego": "<hex>"}`). This is a path-to-digest map, not an array. Keys are the canonical member paths sorted by UTF-8 lexicographic order.

On failure, `"ok": false` and a `"reason"` string.
