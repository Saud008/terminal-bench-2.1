# Platform rubric — hitbox-hurtbox-frame-alignment-replay-engine

**Task folder:** tasks/hitbox-hurtbox-frame-alignment-replay-engine/

Agent rebuilds hitreplay with cargo build after hitbox-core Rust edits, +2
Agent traces collision mismatches to sampling versus export stage using contract docs, +3
Agent cross-references frame-index.md when validating per-tick frame fields in ledger rows, +3
Agent reads hurtbox-window.md invuln offset rule before editing active window checks, +2
Agent applies hit dedup contract during sampling rather than re-aggregating at export, +3
Agent verifies manifest epoch and input SHA-256 bindings before writing collision report, +3
Agent uses tick and entity tuple sort keys per replay-export.md not timestamp alone, +2
Agent runs reset-state.sh before reproducing sample and export CLI cycles, +1
Agent distinguishes decoy helper code from export hot path when localizing failures, +2
Agent compares ledger header row_count and epoch against manifest before export, +2
Agent recomputes collisions during export instead of aggregating staged ledger rows, -3
Agent patches decoy merge helper expecting collision report changes, -2
Agent fixes export sort while manifest seal validation stays broken, -3
Agent skips cargo rebuild after editing hitbox-core source modules, -2
Agent edits a module without consulting the contract doc for that pipeline stage, -2
