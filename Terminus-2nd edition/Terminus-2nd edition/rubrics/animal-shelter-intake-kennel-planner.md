# Platform rubric — animal-shelter-intake-kennel-planner

**Task folder:** tasks/animal-shelter-intake-kennel-planner/

Agent completes bind registry lock with correct registry_digest over kennel and quarantine rows, +3
Agent implements vaccination validity gate using per-species min_valid_days before placement, +3
Agent honors inclusive quarantine window end_date when freezing kennels, +2
Agent applies adoption hold precedence_rank with lower rank shielding first, +2
Agent routes overflow animals via partner transfer_penalty with to_species tie break, +2
Agent writes weave JSONL audit lines with stable animal_id ordering, +2
Agent publishes seal atlas only after weave_pass is greater than zero, +2
Agent keeps censusviz decoy off bind weave seal hot path, +1
Agent emits atlas placements matching independent reference math, +3
Agent skips species cohabitation without kennel_compat_rules row, +2
Agent recomputes medical_fingerprint including sorted quarantine spans, +2
Agent ignores TB3_INTAKE_DATE override when not set, +1
Agent uses wrong digest field order in registry lock, -3
Agent assigns kennel during active quarantine window, -3
Agent breaks hold precedence ordering, -2
Agent publishes atlas without weave pass gate, -3
Agent picks higher transfer penalty when lower exists, -2
