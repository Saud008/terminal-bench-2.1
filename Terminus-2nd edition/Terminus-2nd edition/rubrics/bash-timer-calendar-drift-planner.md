# Platform rubric — bash-timer-calendar-drift-planner

**Task folder:** tasks/bash-timer-calendar-drift-planner/

Agent implements load forecast write-report pipeline with staged manifests under /app/stage/manifests/, +3
Agent merges timer drop-in fragments with basename ascending precedence, +2
Agent normalizes OnCalendar slots through effective timezone into UTC, +3
Agent expands monotonic OnBootSec and OnUnitActiveSec anchors from activation.json, +2
Agent applies RandomizedDelaySec and AccuracySec window bounds per docs, +2
Agent lists persistent catch-up slots in catchup_run_utc before reference_now, +3
Agent computes plan_digest including catchup_run_utc in compact sorted hash payload, +3
Agent exports drift-report.json from staged forecast block not raw bundle replay, +2
Agent refuses write-report when forecast block is missing from manifest, +1
Agent fixes only fragment_merge.py while leaving digest_export.py omitting catchup fields, -3
Agent patches decoy table_print.sh helpers on the export hot path, -3
Agent hashes plan_digest without catchup_run_utc despite export-format contract, -5
Agent writes manifests beside bundle path instead of /app/stage/manifests/, -2
Agent skips hidden persistent and monotonic probe bundles under extra fixture dirs, -2
