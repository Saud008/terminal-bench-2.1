# CLI surface

Binary: `binlim` (installed to `/usr/local/bin/binlim` after build).

## decode

```
binlim decode --input PATH --output PATH --max-depth N --max-bytes N
```

| Flag | Meaning |
|------|---------|
| --input | BLIM file path |
| --output | JSON report path |
| --max-depth | maximum composite nesting (u32) |
| --max-bytes | maximum bytes consumed after header (u64) |

### Success report JSON

```json
{
  "status": "ok",
  "error_code": null,
  "limit_kind": null,
  "value": <decoded tree>,
  "bytes_consumed": <u64>
}
```

`value` uses these shapes:

- null: `null`
- bool: `{"kind":"bool","value":true|false}`
- u32: `{"kind":"u32","value":N}`
- string: `{"kind":"string","value":"..."}`
- vec: `{"kind":"vec","items":[...]}`
- enum: `{"kind":"enum","tag":N,"payload":...}`
- double_option: `{"kind":"double_option","value":null|{"inner":null}|{"inner":{...}}}`

### Error report JSON

```json
{
  "status": "error",
  "error_code": "<code>",
  "limit_kind": "depth"|"bytes"|null,
  "value": null,
  "bytes_consumed": <u64>
}
```

### Exit codes

| Code | When |
|------|------|
| 0 | status ok |
| 2 | limit_exceeded |
| 3 | invalid_varint or invalid_tag |
| 4 | unexpected_eof (truncated input only) |

`limit_exceeded` must use exit code 2 even when the input ends exactly at the limit boundary.
