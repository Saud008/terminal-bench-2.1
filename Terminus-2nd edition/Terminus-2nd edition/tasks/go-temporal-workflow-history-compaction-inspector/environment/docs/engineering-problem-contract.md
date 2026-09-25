# Offline history compaction curator contract

Workflow-ops administrators run a host-local Temporal-like history compaction curator that reconstructs event ordering, activity retry attempts across continue-as-new boundaries, timer pending lanes, compaction seal epochs, SQLite activity exports, and replay risk ledgers from archived history fixtures. Operate wfhistctl under /app with no live cluster connection.
