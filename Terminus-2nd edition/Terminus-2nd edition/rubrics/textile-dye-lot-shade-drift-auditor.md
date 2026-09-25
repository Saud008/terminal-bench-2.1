# Platform rubric — textile-dye-lot-shade-drift-auditor

**Task folder:** tasks/textile-dye-lot-shade-drift-auditor/

Agent implements CIE76 LAB delta with sqrt in AWK, +3
Agent fixes recipe version precedence to pick latest effective_from, +3
Agent walks parent_batch_id chain for target_lab inheritance, +3
Agent applies inclusive rework_end_epoch bounds, +2
Agent makes export-report read correlated staging only, +3
Agent preserves ingest staging readings_digest and correlation_digest, +2
Agent keeps decoy hue_sort_stub off the hot path, +1
Agent documents contracts under /app/docs without instruction hints, +2
Agent runs rebuild-shadedrift before pytest collection, +1
Agent breaks LAB delta math only in sa02, -3
Agent patches export to re-read readings TSV, -3
Agent weakens hidden TB3 trap tests, -5
Agent adds fix-order hints to instruction.md, -3
