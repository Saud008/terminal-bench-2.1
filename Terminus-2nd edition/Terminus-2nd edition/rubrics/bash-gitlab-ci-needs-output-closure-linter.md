# Platform rubric — bash-gitlab-ci-needs-output-closure-linter

**Task folder:** tasks/bash-gitlab-ci-needs-output-closure-linter/

Agent implements matrix key lexicographic sorting for canonical expanded job instance names, +3
Agent applies GitLab first-match-wins rules evaluation stopping after initial matching rule, +3
Agent enforces strict consumer stage index greater than producer stage index for required needs, +3
Agent honors optional true needs edges without missing-job or stage-order errors, +3
Agent computes staging_digest including rules_fingerprint in digest input body, +2
Agent reads gclint-staging.json only during export without re-parsing ingest work files, +3
Agent detects duplicate matrix expansion when permuted axes canonicalize to same instance name, +2
Agent preserves needs arrays with optional and artifacts flags in staging job records, +2
Agent emits export findings sorted by job name then finding code with stable audit_digest, +2
Agent writes artifact paths from job definitions into staging job records during analyze, +2
Agent patches merge_rules_helper believing it participates in ingest or export hot path, -3
Agent uses last-match-wins rules scan leaving inactive jobs marked active in staging, -3
Agent allows test stage jobs to need deploy stage producers without STAGE_ORDER finding, -3
Agent recomputes lint findings from raw YAML inside export_lint.sh bypassing staging snapshot, -3
Agent omits rules_fingerprint from staging digest allowing digest drift across rule changes, -2
