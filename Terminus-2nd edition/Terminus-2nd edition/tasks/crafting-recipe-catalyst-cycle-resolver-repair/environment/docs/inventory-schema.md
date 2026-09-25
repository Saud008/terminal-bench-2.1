# Inventory schema

SQLite database at `/app/work/inventory.db` (created on seed).

## Tables

### `meta`

| key | value |
|-----|-------|
| `slot_limit` | decimal string |
| `last_craft` | last committed recipe id |

### `slots`

| column | type |
|--------|------|
| `slot` | integer primary key |
| `item` | text |
| `qty` | positive integer |

### `craft_log`

Append-only record of committed crafts (`committed = 1`).

Seed wipes and repopulates `slots` and `slot_limit` meta.
