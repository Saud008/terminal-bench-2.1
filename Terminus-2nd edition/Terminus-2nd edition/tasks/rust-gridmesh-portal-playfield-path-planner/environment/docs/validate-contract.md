# Playfield validation contract

## Bidirectional links

Every `edges`, `portals`, and `offmesh` row must appear in the built graph in both directions with the same `cost_q16`.

## Portal regions

When `require_region_match` is true, connected cells must have identical `region` values.

## Off-mesh snap radius

Compute linear Euclidean distance in grid coordinates between endpoint cells. Reject when linear distance exceeds `snap_radius_q16 / 65536`.

Do not compare squared distance to the linear radius threshold.

## Walkable zones

Count walkable connected components using **4-connected** grid adjacency (no diagonals).
