# Recipe book format

JSON object:

```json
{
  "slot_limit": 8,
  "items": [{ "id": "iron_ore", "stack_max": 64, "stackable": true }],
  "substitutes": { "iron_ore": "scrap_iron" },
  "recipes": [
    {
      "id": "smelt_iron",
      "inputs": [{ "item": "iron_ore", "qty": 2 }],
      "catalyst": { "item": "forge_spark", "qty": 1, "consumed": false },
      "output": { "item": "iron_ingot", "qty": 1, "stackable": true }
    }
  ]
}
```

- `slot_limit` — maximum inventory slots.
- `items` — stack metadata used for output placement.
- `substitutes` — optional map from required item id to alternate item id (1:1).
- `catalyst.consumed` defaults to `false`.
