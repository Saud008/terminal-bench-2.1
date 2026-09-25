# Platform rubric — rail-signal-possession-conflict-ledger

**Task folder:** tasks/rail-signal-possession-conflict-ledger/

Agent builds transitive protected-zone map from undirected adjacency, 3
Agent uses half-open minute intervals for possession and reservation overlap, 3
Agent detects possession overlap via protected-zone intersection not exact block equality, 3
Agent clips conflict windows to overlapping half-open interval bounds, 2
Agent applies signal restrict aspect against adjacent protected reservation zones, 3
Agent suppresses lower-priority claims when emergency override zones intersect, 3
Agent increments load_generation on each compile-trackgraph for same seed, 2
Agent sorts conflict group participants with TB3_ZONE_SALT when set, 2
Agent orders conflict blocks by scenario kilometer then block id, 2
Agent sorts exported conflict groups by stable group_key, 2
Agent computes audit_digest with possession_pairs and sorted group_keys, 3
Agent writes trackgraph snapshot to /app/var/rail/trackgraph.snapshot, 2
Agent writes authority ticket during compile-trackgraph staging, 2
Agent rebuilds railpos in test.sh before subprocess pytest, 2
Agent honors TB3_SCENARIO_DIR for hidden rail topology fixtures, 2
Agent uses one-hop adjacency only for protected-zone reachability, -3
Agent treats closed interval endpoints as overlapping for half-open windows, -3
Agent matches signal restrict only when reservation lists exact signal block, -3
Agent suppresses overrides on exact block id match without zone intersection, -2
Agent leaves load_generation unchanged across repeated compile-trackgraph, -2
Agent omits TB3_ZONE_SALT from hidden scenario participant keys, -2
