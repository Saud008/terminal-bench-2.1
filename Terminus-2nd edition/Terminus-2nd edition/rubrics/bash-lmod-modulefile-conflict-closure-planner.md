# Platform rubric — bash-lmod-modulefile-conflict-closure-planner

**Task folder:** tasks/bash-lmod-modulefile-conflict-closure-planner/

Agent implements ingest catalog digest with lexicographic sorting, +3
Agent fixes dependency closure to visit prerequisites before dependents, +3
Agent applies conflict precedence keeping higher @priority modules, +3
Agent emits family swap unloads before replacement loads, +2
Agent exports reproducible load-plan JSON with sorted sequences and plan_digest, +3
Agent wires cross-run ledger idempotency and sequence bumps correctly, +2
Agent patches only decoy wrap helper without fixing export path, -3
Agent hardcodes golden load-plan JSON instead of running export pipeline, -5
Agent edits pytest reference helpers to match broken CLI output, -5
Agent weakens hidden verifier-fixtures tests to pass partial fixes, -3
