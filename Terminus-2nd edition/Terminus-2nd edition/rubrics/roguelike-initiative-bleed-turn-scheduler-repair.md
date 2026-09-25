# Platform rubric — roguelike-initiative-bleed-turn-scheduler-repair

**Task folder:** tasks/roguelike-initiative-bleed-turn-scheduler-repair/

Agent rebuilds turnctl with cargo build after combat-core Rust edits, +2
Agent repairs ingest roster validation to reject negative bleed before staging write, +3
Agent fixes scheduler turn order to sort by initiative then name with pinned actors first, +3
Agent applies bleed damage at start of turn before act or stun events, +3
Agent decrements stunned actors by exactly one action point on stun skip, +2
Agent clears pinned flag when mark_death runs after bleed kills an actor, +2
Agent keeps export transcript event order matching simulate state without reorder merge, +2
Agent implements seed FNV bleed mutation per seed-mutation.md before round one, +2
Agent leaves decoy wrap.rs off ingest simulate export hot path, +1
Agent patches only scheduler while bleed still runs at end of turn, -3
Agent fixes simulate loop but leaves export bleed after act reordering, -3
Agent accepts negative bleed rosters in ingest staging, -2
Agent sorts turn order by actor name only ignoring initiative, -2
Agent skips cargo rebuild after editing combat-core modules, -2
