# Platform rubric — bash-device-node-policy-planner

**Task folder:** tasks/bash-device-node-policy-planner/

Agent implements ingest staging digest from sorted rule token lines plus inherited attrs and match edges, +3
Agent sorts rules by priority source_file line_number not line number alone, +3
Agent merges parent attribute chains before ATTR token matching, +3
Agent matches MODALIAS tokens using catalog glob tags not exact string only, +2
Agent accumulates multiple SYMLINK tokens from one rule line into staging, +2
Agent resolves symlink collision winners using latest effective rule per device, +3
Agent applies OWNER GROUP MODE precedence scanning rules from latest to earliest, +3
Agent formats MODE as four digit octal with leading zeros in export rows, +2
Agent reads match_edges from staging file only during export without re-parsing fixtures, +3
Agent bumps replay.seq only when staging digest changes between ingests, +2
Agent patches decoy merge_apply module believing it is on export hot path, -3
Agent recomputes staging from raw fixture paths inside export_plan.sh, -3
Agent uses earliest-rule-wins permission scan leaving serial overrides wrong, -3
Agent drops hidden i2c sensor-child inheritance symlink coverage, -2
Agent weakens staging digest to device count only, -3
