# Affinity rank rulecard

affinity = 1.0 / (1.0 + haversine_km(focus, document)) with Earth radius 6371.0 km.
Sort by descending affinity, then ascending doc_id.
Keep first max_admit rows; excess become blocked_admit_cap.
