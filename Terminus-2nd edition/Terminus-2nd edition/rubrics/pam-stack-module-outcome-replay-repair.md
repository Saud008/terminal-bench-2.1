# Platform rubric — pam-stack-module-outcome-replay-repair

**Task folder:** tasks/pam-stack-module-outcome-replay-repair/

Agent repairs pamreplay by patching Bash modules under /app/lib/ only, +2
Agent honors PAM control flags requisite required sufficient optional in runner.sh, +3
Agent flattens stack includes within depth limit in stack.sh and compose.sh, +2
Agent commits pam_env changes per phase rules in environment.sh, +2
Agent rolls back committed environment on auth or password failure before audit write, +3
Agent writes globally monotonic audit seq across phases in audit.sh, +2
Agent persists replay.staging.json per staging-contract.md in staging.sh, +2
Agent builds replay.outcome.json with version stack and ordered phases in outcome.sh, +2
Agent validates outcome snapshot before export in outcome_guard.sh, +2
Agent exports JSON from validated outcome snapshot only in export.sh, +3
Agent returns non-zero CLI exit when replay fails even if export file exists, +2
Agent fixes runner.sh only while export still re-executes modules instead of reading snapshot, -3
Agent patches outcome_guard.sh to skip validation so forced zero exit passes, -2
Agent edits export.sh to rebuild phases from stubs instead of outcome artifact, -3
Agent hardcodes catalog stack JSON output instead of running replay pipeline, -3
