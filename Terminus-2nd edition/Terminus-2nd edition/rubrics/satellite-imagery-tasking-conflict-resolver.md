# Platform rubric — satellite-imagery-tasking-conflict-resolver

**Task folder:** tasks/satellite-imagery-tasking-conflict-resolver/

Agent reads pass-window-overlap.md and applies setup padding to overlap checks, +3
Agent implements warm_setup_sec reuse on consecutive same-mode pass assignments, +3
Agent applies strict priority preemption using preempt_rank greater-than comparison, +2
Agent computes cloud_composite using weighted blend from cloud-risk-blend.md, +3
Agent sorts conflict-matrix CSV rows by effective_start_sec then request_id, +2
Agent includes preemption_trace in plan_digest payload per task-plan-manifest-schema.md, +3
Agent stages conflict-matrix CSV with matrix_fingerprint sidecar under /app/var, +2
Agent selects lowest cloud_composite pass among eligible non-overlapping windows, +2
Agent writes scenario bind snapshot to /app/var/scenario-bind during resolve, +1
Agent rebuilds satctl via rebuild-satctl.sh before subprocess pytest invocation, +1
Agent fixes only overlap_guard without correcting cloud_scorer blend formula, -3
Agent uses cold_setup_sec for every assignment ignoring warm mode reuse, -3
Agent omits setup padding when testing pass-window overlap collisions, -5
Agent sorts staging rows by request_id lexically before pass start time, -2
Agent drops preemption_trace from plan_digest hash scope, -3
