# Platform rubric — sqlite-schema-migration-dirty-guard-exporter

**Task folder:** tasks/sqlite-schema-migration-dirty-guard-exporter/

Agent bumps schema version only after a successful up commit, +3
Agent keeps dirty set until failed-version down rollbacks finish, +3
Agent splits multi-statement SQL outside single-quoted literals, +3
Agent holds BEGIN EXCLUSIVE during version ledger export, +3
Agent computes max_version with integer compare on version_log, +3
Agent writes migrate-stage.json with failed_down_rollbacks counter, +2
Agent rebuilds migratectl after editing apply and export modules, +1
Agent honors dirty guard blocking a second up while dirty remains, +2

Agent patches statement split only while version still advances at up start, -3
Agent clears dirty before journal down rollback steps execute, -3
Agent exports lexicographic string max instead of integer max version, -3
Agent fixes export lock only while literal semicolon inserts still fail, -3
