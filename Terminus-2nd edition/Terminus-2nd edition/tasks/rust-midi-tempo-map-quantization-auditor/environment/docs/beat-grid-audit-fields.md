# Beat grid audit fields

Output files end with -beat-grid-audit.json. Fields include run_id, chart_id, ppq, tempo_event_count, accepted_note_count, rejected_overlap_count, grid_consistency_score, notes array, and audit_digest. grid_consistency_score is the fraction of accepted non-rejected notes that are grid-consistent. audit_digest is SHA256 hex over deterministic JSON with sorted source_ids, accepted_note_count, rejected_overlap_count, chart_id, and run_id. Pytest reference helpers may import Python hashlib to recompute the same digest.
