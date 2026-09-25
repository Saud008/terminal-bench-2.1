survey-snapshot.json holds snapshot_version, table_suffix, mesh_id, survey_id, records, final_tally, total_weighted, partial_respondents, export_ready.

survey.manifest mirrors the same JSON for export. Written early before event processing begins with empty records.

Export reads survey.manifest only.
