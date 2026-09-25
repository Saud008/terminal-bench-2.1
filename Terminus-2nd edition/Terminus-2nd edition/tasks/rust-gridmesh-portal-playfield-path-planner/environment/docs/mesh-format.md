# Playfield board bundle format

JSON file with grid cells and playfield navigation links.

## cells[]

| Field | Type | Meaning |
|-------|------|---------|
| `id` | string | Unique cell id |
| `gx`, `gy` | int | Grid coordinates |
| `walkable` | bool | Included in walkable-zone flood fill when true |
| `region` | u16 | Region tag for portal contracts |

## edges[]

Tile-local edges with `cost_q16` in Q16.16 fixed units (`65536` = 1.0 cell).

## portals[]

| Field | Meaning |
|-------|---------|
| `require_region_match` | When true, `from` and `to` cells must share `region` |

## offmesh[]

| Field | Meaning |
|-------|---------|
| `snap_radius_q16` | Maximum **linear** grid distance between endpoints (Q16.16) |

Seed processing may append one adjacent off-mesh jump link derived from `--seed`.
