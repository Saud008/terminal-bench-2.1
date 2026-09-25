# Export schema

`crafter export --db PATH --out PATH` writes:

```json
{
  "slot_limit": 8,
  "slots": [{ "slot": 1, "item": "iron_ingot", "qty": 4 }],
  "last_craft": "smelt_iron"
}
```

- `slots` sorted by `slot` ascending.
- `last_craft` null when no craft committed.
