# Platform rubric — pharmacy-formulary-priorauth-matrix

**Task folder:** tasks/pharmacy-formulary-priorauth-matrix/

Agent normalizes NDC values to eleven-digit 5-4-2 segments before matrix rows, +3
Agent selects highest-rank RxNorm alias when primary rxnorm is empty, +3
Agent applies plan override with highest priority integer for plan and NDC pair, +3
Agent breaks equal priority ties using latest effective_start on or before as-of, +3
Agent marks step_complete false until every prerequisite NDC is step-complete, +3
Agent writes formulary-staging.json with staging_digest before refresh-db, +2
Agent upserts SQLite matrix_rows so double refresh keeps stable row counts, +2
Agent increments refresh_revision on each successful refresh-db pass, +2
Agent blocks export-matrix when refresh_revision is still zero, +2
Agent sorts exported matrix rows by plan_id then ndc_normalized ascending, +2
Agent seals matrix_digest over sorted row payload fields from the export contract, +2
Agent honors TB3 fixture directory for verifier overlay prior-auth traps, +2
Agent rebuilds formulatrix via verifier-rebuild.sh before subprocess checks, +2
Agent pads NDC by left-stripping digits instead of zero-filling to eleven, -3
Agent treats any active override as winning without priority or date tie-break, -3
Agent exports matrix before refresh-db increments refresh_revision, -3
Agent sorts matrix rows by drug name instead of plan_id and NDC, -3
