# Possession window contract

All maintenance possessions and train reservations use half-open minute windows [start_min, end_min). Touching endpoints do not overlap: [0, 60) and [60, 120) are disjoint.

Two claims temporally conflict only when their half-open windows share at least one minute.

Spatial conflict uses protected-zone overlap from zone_map, not exact block_id equality alone.
