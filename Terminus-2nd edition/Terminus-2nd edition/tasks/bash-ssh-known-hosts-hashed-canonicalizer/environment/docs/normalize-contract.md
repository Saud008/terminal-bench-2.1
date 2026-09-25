# Known-hosts normalization contract

The `kh-normalize` tool reads OpenSSH-style `known_hosts` lines from an input file and writes a merged, canonical output file.

## Input handling

- Skip blank lines and lines whose first non-whitespace character is `#`.
- Trim leading and trailing whitespace on each logical line before parsing.
- Preserve key blobs and comments verbatim aside from the rules below.

## Host field parsing

Each record has optional markers, a host specification, a key type token, a base64 key blob, and an optional comment.

### Markers

- `@revoked` and `@cert-authority` are optional prefix markers separated from the host token by one ASCII space.
- Markers must appear in output when present on the surviving merged record.

### Plain hostnames

- A plain host field is a comma-separated list of host tokens without a leading `|`.
- Each token may be a bare hostname/IP or a bracketed non-default port form `[host]:port`.
- Lowercase only hostname characters inside plain tokens. Do **not** lowercase `@revoked`, `@cert-authority`, key types, key blobs, comments, or hashed host tokens.
- Bracket syntax `[Host.Name]:port` keeps brackets and `:port`; only the hostname inside brackets is lowercased, producing `[host.name]:port`.
- When multiple plain tokens appear, sort tokens lexicographically after normalization and join with commas.

### Hashed hostnames

- Hashed host tokens use OpenSSH form `|1|salt|hash` where `1` is the hash version, and `salt` and `hash` are base64 payloads without whitespace.
- Hashed tokens are case-sensitive; never lowercase any part of `|1|salt|hash`.
- A hashed record must retain all four pipe-separated segments.

## Merge policy

Records are keyed by `(host_spec, key_type, key_blob)` where `host_spec` is either the normalized plain host list or the exact `|1|salt|hash` token, and markers are **not** part of the key.

When duplicate keys appear:

1. Prefer a record **without** `@revoked` over one with `@revoked`.
2. If still tied, keep the record whose comment is lexicographically greatest (ASCII); an absent comment sorts before any non-empty comment.

`@cert-authority` does not affect duplicate resolution except that it must remain on the surviving line when present.

## Output ordering

Emit one normalized line per merged record. Sort records by:

1. `record_class`: plain hosts (`0`) before hashed hosts (`1`).
2. `host_sort_key`:
   - plain: first hostname token after normalization (before comma), compared case-insensitively;
   - for bracketed port tokens `[host]:port`, strip the brackets and `:port` suffix and use only the inner hostname as the sort key (for example `[edge.node]:8022` sorts as `edge.node`, not as the literal token `[edge.node]:8022`);
   - hashed: `salt` base64 string compared case-sensitively.
3. `port`: numeric port from the first plain token, or `0` when absent; hashed records use `0`.
4. `key_type` ASCII ascending.
5. `revoked_flag`: non-revoked (`0`) before revoked (`1`).

Do **not** order output by hash digest alone.

## Output line shape

```
[marker ]host-field key-type key-blob[ comment]
```

Exactly one ASCII space separates fields. Markers, when present, are followed by one space before the host field.

## Config file

`/app/config/normalize.json` controls runtime behavior:

- `merge_duplicates` (boolean, default `true`): when `true`, apply the duplicate merge policy above; when `false`, emit every parsed record without collapsing duplicate keys (still sort output).
- `include_comments` (boolean, default `true`): when `true`, preserve comments on output lines; when `false`, omit comment text from emitted lines.

## Determinism

Given the same input bytes and config, output bytes must be identical across runs.
