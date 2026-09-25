# Membrane batch lineage

Each batch may omit alpha, beta, p_base, t_ref, or q_ref when parent_batch_id is set. Resolve each field by walking parent_batch_id links until a non-null value is found. Defaults when no ancestor defines a field: alpha=1.0, beta=1.0, p_base=0.0, t_ref=25.0, q_ref=100.0.

Batch active hour windows use inclusive bounds: active_from_hour <= hour_index <= active_until_hour selects the batch for that hour.
