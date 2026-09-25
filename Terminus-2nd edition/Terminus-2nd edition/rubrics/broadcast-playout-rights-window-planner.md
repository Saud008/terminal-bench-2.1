# Platform rubric — broadcast-playout-rights-window-planner

**Task folder:** tasks/broadcast-playout-rights-window-planner/

Agent imports scenario bundles into /app/state/active-grid.json via import-grid, +3
Agent writes runway-snapshot.json with runway_digest and rights_contract edges, +3
Agent blocks syndicate-plan when compile-epoch plan_pass is zero, +3
Agent picks narrowest qualifying rights window per overlap contract, +3
Agent applies regional blackout precedence only after rights clearance, +3
Agent preserves ad-break cues across feed-specific program substitution, +3
Agent replaces prior SQLite plan_rows on repeated compile-windows, +3
Agent sorts syndication entries by start_utc then program_id, +3
Agent emits blackout_block and ad_marker_dropped conflicts in conflict-report.json, +3
Agent rebuilds gridplan via compile-gridplan.sh before pytest subprocess checks, +2
Agent uses TB3_FIXTURE_DIR hidden bundles without changing refmath contract, +2
Agent omits rights_contract edges from runway snapshot, -3
Agent allows syndicate-plan while plan_pass remains zero, -3
Agent duplicates SQLite plan_rows on second compile-windows run, -3
Agent evaluates blackout before rights window for the same air time, -3
