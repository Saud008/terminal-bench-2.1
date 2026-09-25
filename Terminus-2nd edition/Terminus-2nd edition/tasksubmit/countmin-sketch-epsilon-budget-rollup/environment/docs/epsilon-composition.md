# Epsilon composition

Each shard publishes an epsilon budget spent while collecting its sketch updates. When merging k shards, sequential composition uses L2 accumulation:

composed_epsilon = sqrt(sum(epsilon_i ^ 2))

The staging snapshot epsilon_lineage object must contain raw_epsilons in shard ingest order and composed_epsilon computed with the formula above. Export copies the same lineage block without recomputing from raw values unless merge_generation changed.

Never sum epsilons linearly across shards.
