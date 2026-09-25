# Spread topology

Before affinity ranking, subtract a spread penalty from each allocation raw affinity score.

Penalty weight is 10 per co-located peer on the same node_id excluding self.

spread_penalty_total in summary is the sum of penalties computed over active allocations after drain and stale filtering.

Placements rank only allocations passing hard node.class constraints. Sort by adjusted affinity score descending, then alloc_id ascending. placement_rank starts at 1.
