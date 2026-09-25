# Platform rubric — elevator-maintenance-callout-dispatcher

**Task folder:** tasks/elevator-maintenance-callout-dispatcher/

Agent loads roster feeds into callout.db without corrupting technician rows, +2
Agent ranks trapped-passenger faults above routine door faults in urgency_scores, +3
Agent matches technician skill_level at the required floor exactly, +2
Agent honors inclusive building access window end minutes, +3
Agent selects gold SLA tier_rank when multiple contracts share a building, +2
Agent sorts bind-roster candidates by descending priority then fault_id, +2
Agent preserves locked assignment rows on second bind-roster pass, +3
Agent emits callout-roster.json with breach_horizon_summary and roster_digest, +2
Agent writes rank-ledger.json during rank-faults staging, +1
Agent rebuilds calloutd via verifier-rebuild.sh before export, +1
Agent patches only decoy carpanel while leaving bind hot path broken, -3
Agent deletes locked assignments before rebinding on rerun, -3
Agent uses exclusive access window end boundary, -2
Agent skips trapped_passengers weight in urgency ladder, -2
Agent publishes roster before callout_pass increments, -2
