# mpiqctl CLI surface

Binary path: /app/bin/mpiqctl

Commands:
- snapshot-load --scenario SCENARIO [--fixture-dir DIR]
- compile-policy --scenario SCENARIO
- apply-holds --scenario SCENARIO
- filter-blackouts --scenario SCENARIO
- score-queue --scenario SCENARIO
- bind-inspectors --scenario SCENARIO
- publish-queue --scenario SCENARIO [--output PATH]

Pipeline order is fixed. publish-queue requires queue_pass greater than zero in /app/state/queue-pass.json before export
