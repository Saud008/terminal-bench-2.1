# Platform rubric — rust-hexmap-fog-visibility-turn-planner

**Task folder:** tasks/rust-hexmap-fog-visibility-turn-planner/

Agent implements playfield CLI load-board through seal-atlas on a Rust tactics playtest baseline, +3
Agent computes axial cube distance as (|dq|+|dr|+|ds|)/2 for vision and ray length, +3
Agent builds LOS rays via greedy cube-distance neighbor walk with lexicographic tie-break, +2
Agent treats intermediate elevation as blocking only when elev is strictly greater than min(obs,tgt), +3
Agent applies class vision radii scout=4 infantry=2 tower=3 default=1, +2
Agent keeps sticky fog cells across reveal-fog calls within the same run, +2
Agent increments fog_generation on each reveal-fog and starts at 0 on load-board, +2
Agent seals atlas visible_cells sorted by ascending q then r with win_condition_met on visible_count >= target_reveal, +2
Agent rebuilds release binary before tests and honors board-overlay directory overrides for hidden ridge fixtures, +1
Agent leaves scout_decoy A* off the load-board place-units resolve-los reveal-fog seal-atlas hot path, +1
Agent introduces new failure modes not covered by plains-01 alone, -2
Agent weakens hidden ridge elevation trap assertions, -3
Agent adds instruction hints naming defect modules or fix recipes, -3
Agent copies an ingest staging export neighbor pipeline unchanged, -5
