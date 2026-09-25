# Platform rubric — port-container-demurrage-clock-ledger

**Task folder:** tasks/port-container-demurrage-clock-ledger/
**Written:** 2026-07-10T06:40:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent loads yard scenarios into SQLite via demurctl load-yard, +2
Agent pauses the dwell clock on customs and terminal hold intervals, +3
Agent applies highest-precedence hold code when holds overlap, +3
Agent excludes terminal closure calendar days from eligible dwell, +3
Agent consumes contracted free-time days before demurrage tiers, +3
Agent applies tier-one through tier-three carrier tariff rates correctly, +3
Agent increments clock_pass only after run-clock-staging completes, +2
Agent blocks publish-invoices when clock_pass is zero, +2
Agent writes clock-staging.json digest before invoice export, +2
Agent rebuilds demurctl via verifier-rebuild.sh before subprocess CLI checks, +2
Agent exercises hidden yard scenarios under TB3 fixture directory, +2
Agent bills hold days as eligible dwell without pause, -3
Agent picks lowest-precedence hold when customs and carrier holds overlap, -3
Agent counts closure days toward demurrage tiers, -3
Agent publishes invoices before clock staging completes, -3
