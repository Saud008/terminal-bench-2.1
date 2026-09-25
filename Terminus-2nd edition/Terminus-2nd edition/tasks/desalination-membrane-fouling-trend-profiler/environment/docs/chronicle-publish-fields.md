# Chronicle publish fields

Output paths end with -fouling-trend-chronicle.json.

chronicle_rows sorted by trend severity rank (critical first, then accelerating, then stable), then hour_index ascending within equal rank.

Each row includes hour_index, batch_id, ndp, trend_class, element_fp where element_fp is first 16 hex chars of SHA-256 over batch_id:hour_index:salinity_ppt:pressure_bar with three decimal salinity and pressure formatting.

summary includes total_readings, critical_count, accelerating_count, stable_count, max_ndp.

batch_lineage_digest is SHA-256 hex over sorted batch_id:parent_batch_id pairs joined by pipe.

chronicle_digest is SHA-256 hex over sorted-key JSON with keys accelerating_count, critical_count, max_ndp, stable_count, total_readings, and ndp_values (sorted list of ndp rounded to four decimals).
