# Platform rubric — renewable-ppa-settlement-engine

**Task folder:** tasks/renewable-ppa-settlement-engine/

Agent floors meter readings to the lower fifteen-minute UTC interval boundary, +3
Agent treats curtailment windows as half-open with inclusive start and exclusive end, +3
Agent selects market price by exact aligned interval_start_utc key match, +3
Agent applies max strike versus market cents for settlement pricing per MWh, +3
Agent subtracts in-period ISO holidays from billing day count, +3
Agent materializes settlement-lines.jsonl staging before invoice rollup export, +3
Agent persists settlement line rows into ppa-settlement.db with scenario meta, +3
Agent excludes curtailed intervals from invoice line_count and totals, +3
Agent produces stable lines_digest on repeated rollup of unchanged staging, +3
Agent rebuilds ppareconctl via verifier-rebuild.sh before subprocess CLI checks, +2
Agent uses ceiling alignment within the hour instead of floor truncation, -3
Agent treats curtailment end timestamp as inclusive for skipped energy, -3
Agent walks prior market rows instead of exact interval key lookup, -3
Agent uses min strike market instead of max for settlement cents, -3
Agent adds holiday count to billing days instead of subtracting holidays, -3
Agent publishes invoice rollup without staged JSONL settlement lines present, -3
