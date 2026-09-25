# Layout manifest schema

JSON layout passed to ecs-migrate apply --layout.

```json
{
  "layout_id": "string",
  "from_version": 0,
  "to_version": 0,
  "components": [
    { "name": "string", "offset": 0, "size": 0, "default_hex": "0x0000" }
  ],
  "migration_steps": [
    {
      "order": 0,
      "op": "string",
      "component": "string",
      "target_chunk": 0,
      "from_archetype": "string"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| layout_id | string | Layout identifier |
| from_version | integer | Source layout version |
| to_version | integer | Target layout version after apply |
| components | array | Component layout definitions |
| components[].name | string | Component name |
| components[].offset | integer | Byte offset in entity payload |
| components[].size | integer | Component size in bytes |
| components[].default_hex | string | Optional default bytes for add steps |
| migration_steps | array | Migration operations; implementations must sort by `order` ascending before apply |
| migration_steps[].order | integer | Ascending execution key; lower values run first among journal-eligible steps |
| migration_steps[].op | string | Operation name (add, move, …) |
| migration_steps[].component | string | Target component or synthetic move label |
| migration_steps[].target_chunk | integer | Destination chunk for move |
| migration_steps[].from_archetype | string | Source signature for move |

Derived value: component_stride = max(offset + size) across components.

Signature string: plus-joined component names whose byte ranges contain any non-zero byte, names sorted lexicographically.
