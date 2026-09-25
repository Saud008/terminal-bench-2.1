# Platform rubric — ics-rrule-occurrence-expander-repair

**Task folder:** tasks/ics-rrule-occurrence-expander-repair/

Agent implements RRULE weekly expansion with BYDAY and INTERVAL stride matching fixture-catalog windows, +3
Agent applies EXDATE filtering after RDATE merge including when both properties are present, +3
Agent enforces COUNT after EXDATE and RDATE merge not on the raw series alone, +3
Agent expands monthly BYSETPOS from day one of the anchor month per ical-expansion-contract.md, +3
Agent suppresses spring-forward gap occurrences during timezone conversion to UTC, +2
Agent compares floating UNTIL inclusively in local time and Z-suffixed UNTIL in UTC, +2
Agent writes SQLite occurrences sorted globally by start_utc then uid with zero-based seq, +2
Agent replaces all prior database rows on each expand run, +1
Agent exits non-zero on malformed calendar input, +1
Agent matches independent procedural seed calendars against harness reference math, +2
Agent patches only weekly.go while leaving monthly BYSETPOS expansion wrong, -3
Agent applies COUNT before EXDATE removal so count-exdate fixtures over-emit rows, -3
Agent keeps decoy merge helper on the export hot path instead of contract merge order, -2
Agent hard-codes bundled fixture timestamps instead of computing from RRULE rules, -3
