# Stack format

Stack files are JSON under `/app/fixtures/stacks/`. Paths in `include` entries are relative to `/app/fixtures/stacks/`.

## Top-level fields

| Field | Description |
|-------|-------------|
| `stack_id` | Stable identifier string |
| `service` | PAM service name (used for logging only) |
| `entries` | Ordered list of module entries and include directives |

## Module entry

```json
{
  "phase": "auth",
  "control": "required",
  "module": "stubs/pam_permit.sh",
  "args": []
}
```

`module` paths are relative to `/app/`.

## Include directive

```json
{ "include": "fragments/common-auth.json" }
```

Included files use the same entry shape and may nest further includes.
