# Atlas publish fields

exceedance_rows sorted by property_id ascending, then blast_id ascending, then sensor_id ascending.

Each row includes blast_id, property_id, sensor_id, distance_m rounded to three decimals in JSON output, attenuated_ppv_mm_s, threshold_mm_s, exceedance_mm_s as max(0, attenuated_ppv_mm_s - threshold_mm_s), and exceeded boolean.

summary includes reading_pairs (row count), exceedance_count (rows where exceeded is true), max_exceedance_mm_s (maximum exceedance_mm_s across rows).

atlas_digest is SHA-256 hex over canonical JSON with keys reading_pairs, exceedance_count, max_exceedance_mm_s, and exceedance_values (sorted list of exceedance_mm_s rounded to four decimals).
