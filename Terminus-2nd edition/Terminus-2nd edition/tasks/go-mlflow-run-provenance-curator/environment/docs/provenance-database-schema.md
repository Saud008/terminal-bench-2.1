# Provenance database schema

Closure bind persists state in /app/work/provenance.db using SQLite.
## curation_runs

One active row exists per seed. Re-running curate bind for the same seed replaces the prior active row even when the scenario changes.

| Column | Type | Notes |
|--------|------|-------|
| run_id | INTEGER PRIMARY KEY AUTOINCREMENT | Curation id returned in export summary JSON |
| seed | TEXT NOT NULL | Active seed |
| scenario | TEXT NOT NULL | Active scenario name |
| focus_run_id | TEXT NOT NULL | Scoped focus run id from staging |
| ingest_seq | INTEGER NOT NULL | ingest_seq copied from staging at bind time |
| created_at | TEXT NOT NULL | Defaults to datetime('now') |

## provenance_summary

Summary block for the curation run. run_id is a foreign key to curation_runs.run_id.

| Column | Type | Notes |
|--------|------|-------|
| run_id | INTEGER PRIMARY KEY | Matches curation_runs.run_id |
| binding_ok | INTEGER NOT NULL | 1 when true, 0 when false |
| epoch_monotonic_ok | INTEGER NOT NULL | 1 when true, 0 when false |
| lineage_depth | INTEGER NOT NULL | Length of lineage closure |
| artifact_count | INTEGER NOT NULL | Artifact count on focus run |
| lineage_chain | TEXT NOT NULL | JSON array of scoped run ids, root-first |

export summary reads the active curation_runs row for the requested seed and scenario and joins provenance_summary on run_id. The staged snapshot scenario and the active curated row must match because only one row stays active for a seed at a time.
