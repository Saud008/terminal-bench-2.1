# Platform rubric — hotel-overbooking-walk-cost-allocator

**Task folder:** tasks/hotel-overbooking-walk-cost-allocator/

Agent ingests scenario SQLite into /app/state/active-hotel.db via open-database, +3
Agent seals capacity snapshot with maintenance-aware capacity_fingerprint digest, +3
Agent blocks export when solve_pass in /app/state/solve-pass.json is zero, +3
Agent treats maintenance blackout windows as inclusive through end_date, +3
Agent ranks demand using cancellation probability and arrival priority, +3
Agent applies loyalty protection_rank so lower numeric tier walks last, +3
Agent allows substitution only to strictly higher room_type rank, +3
Agent picks walk destinations minimizing walk_cost_cents with to_type_id tie break, +3
Agent writes displacement atlas assignments and walks arrays never null, +3
Agent rebuilds overbookctl via verifier-rebuild.sh before pytest CLI checks, +2
Agent uses TB3_NIGHT_DATE override when present for night calendar, +2
Agent treats maintenance end_date as exclusive upper bound, -3
Agent sorts walk rows by descending walk_cost_cents in export atlas, -3
Agent allows substitution to equal or lower room rank, -3
Agent ignores loyalty protection_rank during displacement selection, -3
Agent exports displacement atlas before solve-overbook-plan increments solve_pass, -3
