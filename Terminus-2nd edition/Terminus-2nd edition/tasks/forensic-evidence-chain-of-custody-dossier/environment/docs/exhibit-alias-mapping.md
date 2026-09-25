# Exhibit alias mapping

court_alias maps to exactly one evidence_id per case bundle.

If two aliases reference the same evidence_id that is allowed. If two different evidence_ids share a court_alias, emit alias_collision.
