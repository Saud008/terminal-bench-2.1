# Diagnostic output contract

Audit writes a JSON array with one object per graph_id. Each object lists violations sorted by node_id, then code, then tensor name. totals.violation_count equals the violations array length. totals.tensor_count equals staged tensor rows for that graph.
