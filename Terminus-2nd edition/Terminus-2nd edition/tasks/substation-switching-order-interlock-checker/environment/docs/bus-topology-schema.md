# Bus topology snapshot schema

Each yard.snapshot JSON object contains:

- load_seq: monotonic u64 incremented on every compile-yard for the same cache file
- seed: compile seed string
- scenario: scenario_id from the fixture
- buses: sorted bus_id list
- breakers: array of breaker rows with breaker_id, from_bus, to_bus, initial_state (open|closed)
- energized_sources: bus_id list marked as energized sources at t=0
- adjacency: undirected bus pairs derived from breakers (sorted lexicographically)
