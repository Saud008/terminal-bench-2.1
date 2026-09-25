# Overlap rejection policy

Notes on the same lane overlap when their half-open tick intervals intersect. Interval end equals start tick plus duration. When overlap occurs, reject the note with lexicographically larger id. Rejected notes remain in note ledger with rejected_overlap true and do not count toward accepted_note_count or grid_consistency_score.
