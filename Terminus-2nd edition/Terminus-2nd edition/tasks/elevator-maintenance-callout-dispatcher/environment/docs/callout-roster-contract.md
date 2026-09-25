# Dispatch manifest contract

emit-callout writes callout-roster.json with scenario, roster_epoch_minute, assignments array, breach_horizon_summary object mapping fault_id to breach_horizon_min, and roster_digest sha256 hex over the normalized JSON body before the digest field.

Assignments sort by fault_id ascending in the manifest.
