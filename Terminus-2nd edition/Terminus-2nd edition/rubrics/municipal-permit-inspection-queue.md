# Platform rubric — municipal-permit-inspection-queue

**Task folder:** tasks/municipal-permit-inspection-queue/

Agent implements mpiqctl zoning hold precedence with higher hold_rank winning per district, +3
Agent fixes inclusive blackout end_day so requested_day on boundary remains eligible, +3
Agent corrects violation recency weight decay for composite_score ranking, +2
Agent matches inspector cert_level with inclusive floor against lane min_cert_level, +3
Agent gates publish-queue on queue_pass not publish_pass after score-queue, +2
Agent wires compliance-walk.json and mpiq.journal.jsonl staging artifacts, +2
Agent routes electrical permit types to lane-electrical per permit_routes table, +2
Agent skips hold_blocked permits during bind-inspectors while honoring stable rank ties, +2
Agent rebuilds Go binary via verifier-rebuild.sh before pytest subprocess checks, +1
Agent reads TB3_FIXTURE_DIR hidden bundles without copying fixture trees into /app, +2
Agent leaves citizenportal decoy module off the mpiqctl dispatch hot path, -2
Agent weakens hold_summary join query so blocked districts omit counts, -3
Agent patches only certgate while leaving blackout exclusive-end bug in place, -3
Agent edits bundled pytest expected rows instead of fixing queuepublish digest path, -5
Agent adds instruction hints listing internal module filenames for agents to patch, -3
