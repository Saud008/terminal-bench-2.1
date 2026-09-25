# Platform rubric — carbon-intensity-workload-shift-planner

**Task folder:** tasks/carbon-intensity-workload-shift-planner/

Agent normalizes UTC slot windows with half-open end_minute boundaries, 3
Agent rolls unused regional quota into carry_in capped by max_carryover, 3
Agent enforces data-residency allow lists before scheduling, 3
Agent treats deadline_slot as inclusive completion bound, 3
Agent sums intensity across every occupied slot for carbon_mass_g, 3
Agent emits RESIDENCY DEADLINE QUOTA infeasibility_witness reason codes, 2
Agent checks quota availability with rolling carryover during placement, 3
Agent reads shift-staging.json only during export not raw scenarios, 2
Agent sorts assignments and infeasibility_witness by job_id, 2
Agent writes quota_ledger rows sorted by region then window_index, 2
Agent rebuilds shift-pl in test.sh before subprocess pytest, 2
Agent honors SHIFT_SCENARIO_ROOT for hidden verifier fixtures, 2
Agent materializes staging_digest on stage subcommand, 2
Agent picks lowest carbon_mass_g tie-breaking by region and start_slot, 2
Agent ignores lex_rank decoy module on ingest export hot path, 1
Agent hardcodes bundled region alias strings in export output, -3
Agent uses inverted residency allow-list membership test, -3
Agent scores carbon from start slot intensity only, -2
Agent drops carry_out quota between planning windows, -3
Agent treats deadline as strict less-than without inclusive slot, -2
